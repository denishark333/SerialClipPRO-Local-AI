import os
from core.textos import tr
import shutil
import time
import threading
import re
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from core.context_pipeline import REPORT_DIR
from core.clip_order import chave_corte
import json
from api.models import PipelineRequest, StudioConfigRequest, ExportRequest, ReferenciaRequest
from core.pipeline import executar_pipeline_background, gerar_preview_estudio, eh_url_twitch, obter_chave_unica
from core.execution import reservar_execucao, finalizar_execucao, solicitar_cancelamento
from core.config import (
    estado_pipeline, formatar_tempo, carregar_config_estudio, 
    salvar_config_estudio, PASTA_DESTINO, PASTA_EXPORTADOS, PASTA_TEMP, estado_lock
)

router = APIRouter()

preview_lock = threading.Lock()
previews_ativos = set()
# Motivo da última falha de cada preview, para o estúdio parar de esperar e avisar.
previews_erros = {}


@router.post('/selecionar-video')
def selecionar_video(request: Request):
    from core.file_picker import selecionar_video as escolher
    if not request.client or request.client.host not in ('127.0.0.1', '::1', 'testclient'):
        raise HTTPException(403, tr('seletor.so_local'))
    origin = request.headers.get('origin')
    permitidas = {str(request.base_url).rstrip('/'), 'http://localhost:5173', 'http://127.0.0.1:5173'}
    permitidas.update(o.strip() for o in os.getenv('CLIPPRO_ALLOWED_ORIGINS', '').split(',') if o.strip())
    if origin and origin not in permitidas:
        raise HTTPException(403, tr('seletor.origem'))
    try:
        return {'caminho': escolher()}
    except Exception as erro:
        raise HTTPException(503, tr('seletor.falhou', erro=erro)) from erro


def executar_preview(entrada, nome_arquivo):
    try:
        return gerar_preview_estudio(entrada, nome_arquivo,
                                     ao_falhar=lambda motivo: previews_erros.__setitem__(nome_arquivo, motivo))
    finally:
        with preview_lock:
            previews_ativos.discard(nome_arquivo)

@router.post("/iniciar-pipeline")
def iniciar_pipeline(data: PipelineRequest, background_tasks: BackgroundTasks):
    execucao = reservar_execucao()
    if execucao is None:
        raise HTTPException(status_code=409, detail=tr('pipeline.ja_em_execucao'))
    try:
        background_tasks.add_task(executar_pipeline_background, data.entrada, data.max_cortes, execucao, data.ignorar_inicio_segundos,
                                  modo_curadoria=data.modo_curadoria, termos_jogo=data.termos_jogo,
                                  limite_amostras=data.limite_amostras, idioma=data.idioma, foco=data.foco)
    except Exception:
        finalizar_execucao(execucao)
        raise
    return {"mensagem": tr('pipeline.iniciado'), "modo_curadoria": data.modo_curadoria}


@router.get("/relatorios-curadoria/{nome}")
def obter_relatorio_curadoria(nome: str):
    if not re.fullmatch(r"[0-9a-f]{32}\.json", nome):
        raise HTTPException(status_code=404, detail=tr('galeria.relatorio_ausente'))
    caminho = REPORT_DIR / nome
    if not caminho.is_file():
        raise HTTPException(status_code=404, detail=tr('galeria.relatorio_ausente'))
    return FileResponse(caminho, media_type="application/json", filename=nome)

@router.post("/gerar-preview")
def disparar_geracao_preview(data: PipelineRequest, background_tasks: BackgroundTasks):
    """Gera o preview do estúdio de forma isolada, aplicando Cache Hit/Miss inteligente."""
    try:
        if not data.entrada:
            raise HTTPException(status_code=400, detail=tr('preview.entrada_invalida'))

        chave_vod = obter_chave_unica(data.entrada)
        nome_arquivo = f"preview_{chave_vod}.mp4"
        os.makedirs(PASTA_TEMP, exist_ok=True)
        caminho_completo = os.path.join(PASTA_TEMP, nome_arquivo)

        if os.path.exists(caminho_completo) and os.path.getsize(caminho_completo) > 0:
            print(f"⚡ [Cache Hit] Preview já existe para a chave: {chave_vod}")
            return {
                "status": "sucesso",
                "mensagem": tr('preview.cache'),
                "preview_url": f"/temp_clip_cache/{nome_arquivo}"
            }

        print(f"🎬 [Cache Miss] A gerar novo preview exclusivo para a chave: {chave_vod}")
        with preview_lock:
            if nome_arquivo not in previews_ativos:
                previews_erros.pop(nome_arquivo, None)
                previews_ativos.add(nome_arquivo)
                background_tasks.add_task(executar_preview, data.entrada, nome_arquivo)

        return {
            "status": "processando",
            "mensagem": tr('preview.iniciado'),
            "preview_url": f"/temp_clip_cache/{nome_arquivo}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stop-pipeline")
def stop_pipeline():
    solicitado = solicitar_cancelamento()
    return {"status": "cancelando" if solicitado else "ocioso",
            "mensagem": tr('pipeline.cancelamento') if solicitado else tr('pipeline.nada_ativo')}

@router.get("/status")
def obter_status():
    with estado_lock:
        if estado_pipeline["executando"]:
            estado_pipeline["tempo_decorrido"] = formatar_tempo(time.time() - estado_pipeline["tempo_inicio"])
        return {**estado_pipeline, "videos": list(estado_pipeline["videos"])}

@router.get("/studio-config")
def get_studio_config():
    return carregar_config_estudio()

@router.post("/studio-config")
def save_studio_config(config: StudioConfigRequest):
    try:
        novo_config = config.model_dump()
        novo_config["enquadramento_feito"] = True
        
        salvar_config_estudio(novo_config)
        estado_pipeline["enquadramento_feito"] = True
        
        return {"mensagem": tr('estudio.salvo')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _midia_do_editor(url):
    """Arquivo local por trás da URL de mídia do editor; só aceita as duas origens conhecidas."""
    from pathlib import Path
    from urllib.parse import urlparse
    from core import review
    caminho = urlparse(url).path
    if m := re.fullmatch(r'/temp_clip_cache/([\w.\-]+)', caminho):
        arquivo = (Path(PASTA_TEMP) / m.group(1)).resolve()
        if arquivo.parent != Path(PASTA_TEMP).resolve():
            return None
        return arquivo
    if m := re.fullmatch(r'/api/revisao/clips/([0-9a-f]{32})/original', caminho):
        return review.pasta(m.group(1)) / 'original.mp4'
    return None


@router.post("/studio/referencia")
def criar_referencia(pedido: ReferenciaRequest):
    """Assinatura do plano aberto (para o Podcast automático) a partir do quadro do editor.

    Calculada pelo mesmo FFmpeg que compara os planos no render, para as duas baterem.
    """
    import base64
    import subprocess
    from core import planos
    from core.execution import executar_comando
    try:
        arquivo = _midia_do_editor(pedido.midia)
    except ValueError:
        arquivo = None
    if arquivo is None or not arquivo.is_file():
        raise HTTPException(status_code=400, detail=tr('estudio.referencia_midia'))
    rodar = lambda comando, binario=False: executar_comando(  # noqa: E731
        comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=not binario, timeout=60)
    assinatura = planos.assinatura(arquivo, pedido.tempo, rodar)
    miniatura = rodar(['ffmpeg', '-v', 'error', '-ss', f'{pedido.tempo:.3f}', '-i', str(arquivo), '-frames:v', '1',
                       '-vf', 'scale=192:-2', '-f', 'image2pipe', '-c:v', 'mjpeg', '-q:v', '5', '-'], binario=True)
    if assinatura is None or miniatura.returncode != 0 or not miniatura.stdout:
        raise HTTPException(status_code=400, detail=tr('estudio.referencia_midia'))
    # Preview do estúdio: a chave do vídeo vai junto, para a referência não valer em outro vídeo.
    nome = arquivo.name
    origem = nome[len('preview_'):-len('.mp4')] if nome.startswith('preview_') and nome.endswith('.mp4') else None
    return {'referencia': base64.b64encode(assinatura).decode(), 'origem': origem,
            'miniatura': 'data:image/jpeg;base64,' + base64.b64encode(miniatura.stdout).decode()}


@router.get("/studio/frame-base")
def get_frame_base(entrada: str = Query(None)):
    """Busca o ficheiro de vídeo real correspondente à VOD/link atual na pasta temp."""
    try:
        os.makedirs(PASTA_TEMP, exist_ok=True)
        
        # 1. Se NÃO há entrada ou está vazia, retorna diretamente a logo estática
        if not entrada or not entrada.strip():
            return JSONResponse(content={"url": "/serial-healer.png", "tipo": "estatico"})
        
        # 2. Busca estritamente o preview correspondente a ESTE link exato
        chave_vod = obter_chave_unica(entrada)
        nome_especifico = f"preview_{chave_vod}.mp4"
        caminho_especifico = os.path.join(PASTA_TEMP, nome_especifico)
        
        if os.path.exists(caminho_especifico) and os.path.getsize(caminho_especifico) > 0:
            return JSONResponse(content={
                "url": f"/temp_clip_cache/{nome_especifico}",
                "tipo": "video_real"
            })
        
        # 3. A geração falhou: o estúdio para de esperar e mostra o motivo.
        if nome_especifico in previews_erros and nome_especifico not in previews_ativos:
            return JSONResponse(content={"url": "/serial-healer.png", "tipo": "erro",
                                         "mensagem": previews_erros[nome_especifico]})

        # 4. Se o preview específico ainda não existe, retorna a logo estática
        return JSONResponse(content={"url": "/serial-healer.png", "tipo": "estatico"})
        
    except Exception as e:
        return JSONResponse(content={"url": "/serial-healer.png", "tipo": "estatico"})

@router.get("/clips")
def listar_clips():
    """Endpoint para o FrontEnd consultar e carregar os cortes salvos na pasta automaticamente."""
    try:
        clips = []
        if os.path.exists(PASTA_DESTINO):
            for f in sorted(os.listdir(PASTA_DESTINO), key=chave_corte):
                if f.endswith(".mp4"):
                    curadoria = None
                    try:
                        with open(os.path.join(PASTA_DESTINO, f + ".json"), encoding="utf-8") as arquivo:
                            curadoria = json.load(arquivo)
                    except (OSError, ValueError):
                        pass
                    clips.append({
                        "nome": f,
                        "url": f"/videos/{f}",
                        "curadoria": curadoria,
                    })
        return {"clips": clips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exportar-selecionados")
def exportar_selecionados(payload: ExportRequest):
    """Copia os clipes marcados por checkbox para a pasta segura de exportação definitiva."""
    try:
        exportados_com_sucesso = []
        for caminho_relativo in payload.videos:
            nome_arquivo = os.path.basename(caminho_relativo)
            origem = os.path.join(PASTA_DESTINO, nome_arquivo)
            destino = os.path.join(PASTA_EXPORTADOS, nome_arquivo)
            
            if os.path.exists(origem):
                shutil.copy2(origem, destino)
                exportados_com_sucesso.append(nome_arquivo)
            else:
                print(f"⚠️ Ficheiro não encontrado para exportar: {origem}")
                
        return {
            "mensagem": tr('galeria.exportados', total=len(exportados_com_sucesso)),
            "pasta_destino": PASTA_EXPORTADOS,
            "arquivos": exportados_com_sucesso
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deletar-selecionados")
def deletar_selecionados(payload: ExportRequest):
    """Repete bloqueios por lote, com espera limitada para toda a requisicao."""
    pendentes = list(dict.fromkeys(os.path.basename(p) for p in payload.videos))
    if any(not n.lower().endswith('.mp4') or ':' in n or n in ('.', '..') for n in pendentes):
        raise HTTPException(status_code=400, detail=tr('galeria.nome_invalido'))
    apagados, ausentes, falhas, avisos = [], [], [], []
    for tentativa in range(5):
        bloqueados = []
        for nome in pendentes:
            caminho = os.path.join(PASTA_DESTINO, nome)
            try:
                os.unlink(caminho)
            except FileNotFoundError:
                ausentes.append(nome)
                continue
            except PermissionError:
                if tentativa < 4:
                    bloqueados.append(nome)
                else:
                    falhas.append({"nome": nome, "motivo": tr('galeria.em_uso')})
                continue
            except OSError as erro:
                falhas.append({"nome": nome, "motivo": str(erro)})
                continue
            apagados.append(nome)
            try:
                os.unlink(caminho + '.json')
            except FileNotFoundError:
                pass
            except OSError:
                avisos.append({"nome": nome, "motivo": tr('galeria.metadados')})
        pendentes = bloqueados
        if not pendentes:
            break
        time.sleep(0.3)
    return {"mensagem": tr('galeria.excluidos', apagados=len(apagados), falhas=len(falhas), ausentes=len(ausentes)),
            "arquivos": apagados, "ausentes": ausentes, "falhas": falhas, "avisos": avisos}
