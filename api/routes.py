import os
import shutil
import time
import threading
import re
import hashlib
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from core.context_pipeline import REPORT_DIR
from core.clip_order import chave_corte
import json
from api.models import PipelineRequest, StudioConfigRequest, ExportRequest
from core.pipeline import executar_pipeline_background, gerar_preview_estudio, eh_url_twitch
from core.execution import reservar_execucao, finalizar_execucao, solicitar_cancelamento
from core.config import (
    estado_pipeline, formatar_tempo, carregar_config_estudio, 
    salvar_config_estudio, PASTA_DESTINO, PASTA_EXPORTADOS, PASTA_TEMP, estado_lock
)

router = APIRouter()

preview_lock = threading.Lock()
previews_ativos = set()


@router.post('/selecionar-video')
def selecionar_video(request: Request):
    from core.file_picker import selecionar_video as escolher
    if not request.client or request.client.host not in ('127.0.0.1', '::1', 'testclient'):
        raise HTTPException(403, 'O seletor está disponível somente neste computador.')
    origin = request.headers.get('origin')
    permitidas = {str(request.base_url).rstrip('/'), 'http://localhost:5173', 'http://127.0.0.1:5173'}
    permitidas.update(o.strip() for o in os.getenv('CLIPPRO_ALLOWED_ORIGINS', '').split(',') if o.strip())
    if origin and origin not in permitidas:
        raise HTTPException(403, 'Origem não permitida.')
    try:
        return {'caminho': escolher()}
    except Exception as erro:
        raise HTTPException(503, 'Não foi possível abrir o seletor de arquivos: ' + str(erro)) from erro


def executar_preview(entrada, nome_arquivo):
    try:
        return gerar_preview_estudio(entrada, nome_arquivo)
    finally:
        with preview_lock:
            previews_ativos.discard(nome_arquivo)

def obter_chave_unica(entrada: str) -> str:
    """Extrai o ID da VOD da Twitch ou gera um hash único seguro para qualquer outra URL/ficheiro."""
    if not entrada:
        return "default"
    
    # Tenta extrair o ID numérico de uma VOD da Twitch (ex: twitch.tv/videos/2875327192)
    twitch_match = re.search(r"videos/(\d+)", entrada)
    if eh_url_twitch(entrada):
        identificador = twitch_match.group(1) if twitch_match else hashlib.md5(entrada.strip().encode('utf-8')).hexdigest()
        # A nova chave impede reutilizar previews antigos extraídos no minuto 1.
        return f"twitch_{identificador}_30m_10s"
    
    # Para outros links ou caminhos de ficheiro locais, cria um hash MD5 único
    return hashlib.md5(entrada.strip().encode('utf-8')).hexdigest()

@router.post("/iniciar-pipeline")
def iniciar_pipeline(data: PipelineRequest, background_tasks: BackgroundTasks):
    execucao = reservar_execucao()
    if execucao is None:
        raise HTTPException(status_code=409, detail="Pipeline em execução ou encerrando. Aguarde.")
    try:
        background_tasks.add_task(executar_pipeline_background, data.entrada, data.max_cortes, execucao, data.ignorar_inicio_segundos,
                                  modo_curadoria=data.modo_curadoria, termos_jogo=data.termos_jogo,
                                  limite_amostras=data.limite_amostras, idioma=data.idioma, foco=data.foco)
    except Exception:
        finalizar_execucao(execucao)
        raise
    return {"mensagem": "Pipeline iniciado.", "modo_curadoria": data.modo_curadoria}


@router.get("/relatorios-curadoria/{nome}")
def obter_relatorio_curadoria(nome: str):
    if not re.fullmatch(r"[0-9a-f]{32}\.json", nome):
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    caminho = REPORT_DIR / nome
    if not caminho.is_file():
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    return FileResponse(caminho, media_type="application/json", filename=nome)

@router.post("/gerar-preview")
def disparar_geracao_preview(data: PipelineRequest, background_tasks: BackgroundTasks):
    """Gera o preview de 10 segundos de forma isolada, aplicando Cache Hit/Miss inteligente."""
    try:
        if not data.entrada:
            raise HTTPException(status_code=400, detail="URL ou entrada inválida.")

        chave_vod = obter_chave_unica(data.entrada)
        nome_arquivo = f"preview_{chave_vod}.mp4"
        os.makedirs(PASTA_TEMP, exist_ok=True)
        caminho_completo = os.path.join(PASTA_TEMP, nome_arquivo)

        if os.path.exists(caminho_completo) and os.path.getsize(caminho_completo) > 0:
            print(f"⚡ [Cache Hit] Preview já existe para a chave: {chave_vod}")
            return {
                "status": "sucesso",
                "mensagem": "Preview recuperado do cache instantaneamente.",
                "preview_url": f"/temp_clip_cache/{nome_arquivo}"
            }

        print(f"🎬 [Cache Miss] A gerar novo preview exclusivo para a chave: {chave_vod}")
        with preview_lock:
            if nome_arquivo not in previews_ativos:
                previews_ativos.add(nome_arquivo)
                background_tasks.add_task(executar_preview, data.entrada, nome_arquivo)

        return {
            "status": "processando",
            "mensagem": "Geração do preview do estúdio iniciada em segundo plano.",
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
            "mensagem": "Cancelamento solicitado." if solicitado else "Nenhuma execução ativa."}

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
        
        return {"mensagem": "Configuração salva; será aplicada aos próximos cortes renderizados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        
        # 3. Se o preview específico ainda não existe, retorna a logo estática
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
            "mensagem": f"{len(exportados_com_sucesso)} cortes exportados com segurança!",
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
        raise HTTPException(status_code=400, detail="Nome de corte invalido.")
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
                    falhas.append({"nome": nome, "motivo": "Arquivo em uso ou sem permissao para excluir."})
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
                avisos.append({"nome": nome, "motivo": "Video excluido; metadados nao puderam ser removidos."})
        pendentes = bloqueados
        if not pendentes:
            break
        time.sleep(0.3)
    return {"mensagem": f"{len(apagados)} corte(s) excluido(s). {len(falhas)} nao puderam ser excluidos. {len(ausentes)} ja estavam ausentes.",
            "arquivos": apagados, "ausentes": ausentes, "falhas": falhas, "avisos": avisos}
