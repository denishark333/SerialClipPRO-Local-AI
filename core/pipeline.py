import os
from core.textos import tr
import time
import json
import subprocess
import tempfile
import uuid
import math
from urllib.parse import urlsplit
import yt_dlp

from core.config import (
    PASTA_TEMP, PASTA_DESTINO,
    estado_pipeline, estado_lock, atualizar_estado,
    carregar_config_estudio, formatar_tempo
)
from core.branding import snapshot as snapshot_marca, filtro_marca, estilo_legenda
from core.downloader import obter_url_direta_cdn, obter_fontes_cdn, extrair_info, recusar_live
from core.context_pipeline import preparar_cortes_contextuais, REPORT_DIR, AMOSTRADOS
from core.transcription import salvar_json
from core.subtitles import filtro_legenda, escrever_legenda
from core.composition import compor_video
from core.review import guardar as guardar_base_revisao
from core.curation_status import verificar_ollama, mensagem_conclusao
from core.encoders import renderizar, medir_volume, args_audio
from core.ia import modelo as modelo_ia
from core.erros import ErroFFmpeg
from core.audio import medir_duracao

from core.execution import (
    executar_comando, reservar_execucao, finalizar_execucao, PipelineCancelado,
)

def limpar_url_youtube(url: str) -> str:
    """Remove parâmetros de playlist/rádio da URL do YouTube, mantendo apenas o ID do vídeo."""
    if not isinstance(url, str):
        return str(url or "")
    url = url.strip()
    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        return url
    try:
        parsed = urlsplit(url)
        if parsed.query:
            params = [part for part in parsed.query.split("&") if part.startswith("v=")]
            if params:
                return f"https://www.youtube.com/watch?{params[0]}"
    except ValueError:
        pass
    return url

def obter_stream_youtube(url_limpa, incluir_audio=False):
    ydl_opts_url = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    
    info = extrair_info(ydl_opts_url, url_limpa)
    if 'entries' in info:
        info = info['entries'][0]
    recusar_live(info)

    # Pega a URL de streaming dinamicamente de forma segura
    video_streaming_url = info.get('url')
    if not video_streaming_url and 'formats' in info:
        # Fallback para o melhor formato URL disponível na lista
        formats = info['formats']
        for f in reversed(formats):
            if f.get('url') and f.get('vcodec') != 'none':
                video_streaming_url = f['url']
                break

    if not video_streaming_url:
        raise Exception(tr('link.sem_stream'))
    if incluir_audio:
        formatos = list(info.get('formats') or []) + list(info.get('requested_formats') or [])
        audio = next((f['url'] for f in reversed(formatos)
                      if f.get('url') and f.get('acodec') not in (None, 'none') and f.get('vcodec') == 'none'), None)
        if not audio:
            audio = next((f['url'] for f in reversed(formatos)
                          if f.get('url') and f.get('acodec') not in (None, 'none')), None)
        if not audio and info.get('acodec') not in (None, 'none'):
            audio = info.get('url')
        if not audio:
            raise ValueError(tr('link.sem_audio_hibrido'))
        return audio, video_streaming_url
        
    return video_streaming_url


def preparar_origem_youtube(entrada: str, pasta_temp: str, execucao=None):
    """Baixa apenas o áudio rapidamente para análise e obtém a URL de streaming do vídeo para cortes sob demanda."""
    url_limpa = limpar_url_youtube(entrada)
    caminho_audio_local = os.path.join(pasta_temp, "origem.m4a")
    
    print(f"📥 Baixando apenas o áudio do YouTube para análise rápida: {url_limpa}")
    
    # Sem restrições rígidas de formato para evitar o erro "Requested format is not available"
    ydl_opts_audio = {
        'outtmpl': caminho_audio_local.replace('.m4a', ''),
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
    }
    
    if execucao:
        execucao.verificar()
        ydl_opts_audio['progress_hooks'] = [execucao.progresso_download]
        ydl_opts_audio['postprocessor_hooks'] = [execucao.progresso_download]

    try:
        # Antes do download: recusa lives, que nunca terminariam de baixar.
        video_streaming_url = obter_stream_youtube(url_limpa)
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([url_limpa])

        if execucao:
            execucao.verificar()

        # Garante que o arquivo m4a existe com extensão correta
        if not os.path.exists(caminho_audio_local):
            for f in os.listdir(pasta_temp):
                if f.startswith("origem") and f.endswith(".m4a"):
                    caminho_audio_local = os.path.join(pasta_temp, f)
                    break

        if execucao:
            execucao.verificar()
        if not os.path.isfile(caminho_audio_local):
            raise FileNotFoundError(tr('link.youtube_sem_audio'))
        return caminho_audio_local, video_streaming_url
    except Exception as e:
        if execucao:
            execucao.verificar()
        raise Exception(tr('link.youtube_falhou', erro=str(e)))

def obter_dimensoes_video(caminho_ou_url, execucao=None):
    """Obtém largura e altura reais do vídeo usando ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "json", caminho_ou_url
        ]
        res = executar_comando(cmd, execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            stream = data["streams"][0]
            return int(stream["width"]), int(stream["height"])
    except Exception as e:
        if execucao:
            execucao.verificar()
        print(f"⚠️ Erro ao obter dimensões via ffprobe: {e}. Usando padrão 1920x1080.")
    return 1920, 1080

def executar_pipeline_background(entrada: str, max_cortes: int, execucao=None, ignorar_inicio_segundos=600, modo_curadoria="picos", termos_jogo="", limite_amostras=40, idioma="pt", foco=""):
    execucao = execucao or reservar_execucao()
    if execucao is None:
        raise RuntimeError(tr('pipeline.em_andamento'))
    temporarios = None
    detalhe_erro = None
    marco_etapa = time.monotonic()
    etapa_medida = "preparacao_origem"
    tempos = {}
    try:
        execucao.verificar()
        temporarios = tempfile.TemporaryDirectory(prefix="pipeline_", dir=PASTA_TEMP)
        pasta_temp = temporarios.name
        marca = snapshot_marca(pasta_temp)
        estilo = estilo_legenda()  # fixado no início: mudar a aba Marca no meio não mistura estilos
        config_estudio = carregar_config_estudio()
        print('[Marca] ' + ('Ativa nesta execução.' if marca else 'Desativada ou sem imagem nesta execução.'))
        entrada = entrada.strip().strip('"').strip("'")
        if not entrada or not 1 <= max_cortes <= 50:
            raise ValueError(tr('pipeline.entrada_invalida'))
        modelo_llm = modelo_ia()
        atualizar_estado(tr('status.verificando_ollama', modelo=modelo_llm), 1, 1)
        verificar_ollama(execucao, modelo_llm)
        print(f'[Curadoria] Ollama respondeu e {modelo_llm} está instalado. Iniciando preparação da mídia.')
        # Rascunhos existentes permanecem disponíveis até exclusão explícita.
        # -------------------------------------------------------------
        # PASSO 1: Obtenção inteligente (Áudio leve para YT / CDN / Local)
        # -------------------------------------------------------------
        atualizar_estado(tr('status.passo1'), 1, 10)
        
        audio_analise_path = None
        video_corte_fonte = None

        if entrada.startswith("http://") or entrada.startswith("https://"):
            if "youtube.com" in entrada or "youtu.be" in entrada:
                if modo_curadoria in AMOSTRADOS:
                    audio_analise_path, video_corte_fonte = obter_stream_youtube(limpar_url_youtube(entrada), incluir_audio=True)
                else:
                    audio_analise_path, video_corte_fonte = preparar_origem_youtube(entrada, pasta_temp, execucao)
                print("✅ Fontes de áudio e vídeo do YouTube preparadas.")
            else:
                audio_analise_path, video_corte_fonte = obter_fontes_cdn(entrada)
                print("✅ Link CDN da Twitch/Kick obtido com sucesso."
                      + (" Análise usará só o áudio." if audio_analise_path != video_corte_fonte else ""))
        else:
            caminho_alvo = entrada
            if not os.path.exists(caminho_alvo):
                caminho_downloads = os.path.expanduser("~\\Downloads")
                caminho_alvo = os.path.join(caminho_downloads, os.path.basename(entrada))
            
            if os.path.exists(caminho_alvo):
                video_corte_fonte = os.path.abspath(caminho_alvo)
                audio_analise_path = video_corte_fonte
                print(f"📁 Utilizando ficheiro local: {video_corte_fonte}")
            else:
                raise FileNotFoundError(tr('pipeline.arquivo_ausente', entrada=entrada))

        orig_w, orig_h = obter_dimensoes_video(video_corte_fonte, execucao)
        print(f"📺 Resolução de origem detectada pelo pipeline: {orig_w}x{orig_h}")

        # -------------------------------------------------------------
        # PASSO 2: Mapeamento Inteligente, Transcrição e Curadoria
        # -------------------------------------------------------------
        atualizar_estado(tr('status.passo2'), 2, 30)
        
        tempos[etapa_medida] = time.monotonic() - marco_etapa
        marco_etapa = time.monotonic()
        etapa_medida = "analise_e_extracao"
        if modo_curadoria not in ("contexto", "hibrido", "picos"):
            raise ValueError(tr('pipeline.modo_invalido'))
        # Os três modos usam a mesma curadoria: transcrevem (a fonte inteira ou
        # amostras), avaliam todos os trechos e escolhem os melhores pela nota.
        resolver_video = None
        if entrada.startswith(("http://", "https://")):
            if "youtube.com" in entrada or "youtu.be" in entrada:
                resolver_video = lambda: obter_stream_youtube(limpar_url_youtube(entrada),
                                                              incluir_audio=modo_curadoria in AMOSTRADOS)
            else:
                resolver_video = lambda: obter_fontes_cdn(entrada)
        cortes_validados = preparar_cortes_contextuais(
            entrada, audio_analise_path, video_corte_fonte, pasta_temp,
            max_cortes, execucao, ignorar_inicio_segundos, termos_jogo, resolver_video=resolver_video,
            modo=modo_curadoria, limite_amostras=limite_amostras, idioma=idioma, foco=foco,
        )

        total_validos = len(cortes_validados)
        print(f"🎯 Total de ganchos liberados para curadoria: {total_validos}")

        if total_validos == 0:
            raise Exception(tr('pipeline.sem_gancho'))

        # -------------------------------------------------------------
        # PASSO 3: Geração de Legendas SRT & Renderização Vertical
        # -------------------------------------------------------------
        tempos[etapa_medida] = time.monotonic() - marco_etapa
        marco_etapa = time.monotonic()
        etapa_medida = "renderizacao"
        timestamp_sessao = time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
        videos_gerados = []

        for idx, corte in enumerate(cortes_validados):
            execucao.verificar()
            pct = 50 + int(((idx + 1) / total_validos) * 45)
            atualizar_estado(tr('status.passo3', atual=idx+1, total=total_validos), 3, pct)
            
            output_video = os.path.abspath(os.path.join(pasta_temp, f"corte_{timestamp_sessao}_{idx+1}.mp4"))
            
            srt_param = ""
            srt_path = None
            if corte['palavras'] and len(corte['palavras']) > 0:
                srt_path = os.path.abspath(os.path.join(pasta_temp, f"legenda_corte_{idx+1}.ass"))
                try:
                    escrever_legenda(srt_path, corte['palavras'], estilo)

                    srt_param = filtro_legenda(srt_path)
                except Exception as e:
                    print(f"⚠️ Erro ao gerar SRT para o corte {idx+1}: {e}")

            filtro, altura_webcam = compor_video(config_estudio, orig_w, orig_h, srt_param)
            map_args = ["-filter_complex", filtro, "-map", "[v_final]", "-map", "0:a"]

            entradas_render = ["ffmpeg", "-y", "-i", corte['trecho_path']]
            if marca:
                entradas_render += ["-i", marca['arquivo']]
                filtro += ';' + filtro_marca(marca, altura_webcam)
                map_args = ["-filter_complex", filtro, "-map", "[v_marca]", "-map", "0:a"]

            def tentativa(nome):
                with estado_lock:
                    estado_pipeline['encoder_tentativa'] = nome

            medida = medir_volume(corte['trecho_path'], lambda comando: executar_comando(
                comando, execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            audio_final = args_audio(medida)
            nome_encoder, res_render = renderizar(
                lambda codec: entradas_render + map_args + codec + audio_final + [output_video],
                lambda comando: executar_comando(comando, execucao=execucao, stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE, text=True),
                f'[Render] Corte {idx+1}', ao_tentar=tentativa)
            with estado_lock:
                estado_pipeline['encoder_tentativa'] = None
                if nome_encoder:
                    estado_pipeline['encoder'] = nome_encoder
            if nome_encoder is None:
                raise ErroFFmpeg(tr('ffmpeg.renderizar', numero=idx+1), res_render.stderr)
            validar_video(output_video, execucao)
            execucao.verificar()
            guardar_base_revisao(corte, os.path.basename(output_video), config_estudio, marca, orig_w, orig_h, timestamp_sessao)
            os.replace(output_video, os.path.join(PASTA_DESTINO, os.path.basename(output_video)))
            if "curadoria" in corte:
                salvar_json(os.path.join(PASTA_DESTINO, os.path.basename(output_video) + ".json"), corte["curadoria"])
            videos_gerados.append(f"/videos/corte_{timestamp_sessao}_{idx+1}.mp4")

            estado_pipeline["videos"] = list(videos_gerados)

        execucao.verificar()
        tempo_total_seg = time.time() - estado_pipeline["tempo_inicio"]
        estado_pipeline["tempo_total"] = formatar_tempo(tempo_total_seg)
        atualizar_estado(mensagem_conclusao(estado_pipeline.get('resumo_curadoria'), estado_pipeline['tempo_total']), 3, 100)

    except PipelineCancelado:
        pass
    except Exception as e:
        tempo_total_seg = time.time() - estado_pipeline["tempo_inicio"] if estado_pipeline["tempo_inicio"] > 0 else 0
        estado_pipeline["tempo_total"] = formatar_tempo(tempo_total_seg)
        print(f"❌ Erro crítico no pipeline: {str(e)}")
        atualizar_estado(tr('status.erro', erro=str(e)), -1, estado_pipeline["progresso_pct"])
        if isinstance(e, ErroFFmpeg):
            detalhe_erro = e.detalhe


    finally:
        tempos[etapa_medida] = time.monotonic() - marco_etapa
        estado_pipeline["tempos_etapas"] = {k: round(v, 2) for k, v in tempos.items()}
        relatorio_url = estado_pipeline.get("relatorio_curadoria")
        if relatorio_url:
            caminho_relatorio = REPORT_DIR / os.path.basename(relatorio_url)
            try:
                dados = json.loads(caminho_relatorio.read_text(encoding="utf-8"))
                dados.update(tempos_etapas=estado_pipeline["tempos_etapas"], videos=estado_pipeline["videos"],
                             resultado_pipeline="cancelado" if execucao.cancelamento.is_set() else estado_pipeline["status"])
                if detalhe_erro:
                    dados.setdefault("erro_detalhe", detalhe_erro)
                salvar_json(caminho_relatorio, dados)
            except (OSError, ValueError) as erro_relatorio:
                print(f"Não foi possível atualizar os tempos do relatório: {erro_relatorio}")
        try:
            if temporarios is not None:
                temporarios.cleanup()
        finally:
            finalizar_execucao(execucao)


def validar_video(caminho, execucao=None, exigir_audio=True):
    resultado = executar_comando([
        "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
        "-of", "json", caminho,
    ], execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
    if resultado.returncode != 0:
        raise RuntimeError(tr('pipeline.video_invalido', erro=resultado.stderr[-1000:]))
    dados = json.loads(resultado.stdout)
    tipos = {s.get("codec_type") for s in dados.get("streams", [])}
    duracao = float(dados.get("format", {}).get("duration", 0))
    exigidos = {"video", "audio"} if exigir_audio else {"video"}
    if not exigidos.issubset(tipos) or not math.isfinite(duracao) or duracao <= 0:
        raise RuntimeError(tr('pipeline.video_incompleto'))


def eh_url_twitch(entrada: str) -> bool:
    url = urlsplit(entrada.strip())
    host = (url.hostname or "").lower()
    return url.scheme in ("http", "https") and (host == "twitch.tv" or host.endswith(".twitch.tv"))


def gerar_preview_estudio(entrada: str, nome_arquivo: str = "preview_10s.mp4", ao_falhar=None):
    """Gera o preview do estúdio; ``ao_falhar`` recebe o motivo quando não dá certo."""
    with tempfile.TemporaryDirectory(prefix="preview_job_", dir=PASTA_TEMP) as pasta_temp:
        return _gerar_preview(entrada, os.path.basename(nome_arquivo), pasta_temp, ao_falhar)


def _gerar_preview(entrada, nome_arquivo, pasta_temp, ao_falhar=None):
    """Extrai o preview de 10 segundos rapidamente sob demanda."""
    try:
        os.makedirs(PASTA_TEMP, exist_ok=True)
        
        if entrada.startswith("http://") or entrada.startswith("https://"):
            if "youtube.com" in entrada or "youtu.be" in entrada:
                video_corte_fonte = obter_stream_youtube(limpar_url_youtube(entrada))
            else:
                video_corte_fonte = obter_url_direta_cdn(entrada)
        else:
            caminho_alvo = entrada
            if not os.path.exists(caminho_alvo):
                caminho_downloads = os.path.expanduser("~\\Downloads")
                caminho_alvo = os.path.join(caminho_downloads, os.path.basename(entrada))
            if os.path.exists(caminho_alvo):
                video_corte_fonte = os.path.abspath(caminho_alvo)
            else:
                raise FileNotFoundError(tr('preview.arquivo_ausente', entrada=entrada))

        trecho_preview_mp4 = os.path.join(pasta_temp, nome_arquivo)
        print(f"📸 [Preview Isolado] Extraindo trecho de 10 segundos para: {nome_arquivo}...")
        
        cmd_preview_10s = [
            "ffmpeg", "-y", "-ss", "00:01:00", "-i", video_corte_fonte,
            "-t", "10", "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", trecho_preview_mp4
        ]
            
        # A metade do vídeo quase sempre mostra a live em andamento, com a webcam: a
        # abertura (Starting Soon) varia de canal para canal e nenhum ponto fixo serve.
        # Sem duração conhecida, valem os pontos antigos (30 min na Twitch, 1 min nos demais).
        inicios = ("00:30:00",) if eh_url_twitch(entrada) else ("00:01:00", "0")
        duracao = medir_duracao(video_corte_fonte)
        if duracao and duracao > 20:
            inicios = (f"{duracao / 2:.3f}",) + inicios
        for tentativa, inicio in enumerate(inicios):
            cmd_preview_10s[3] = inicio
            try:
                executar_comando(cmd_preview_10s, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                validar_video(trecho_preview_mp4, exigir_audio=False)
                break
            except (RuntimeError, subprocess.CalledProcessError):
                if tentativa == len(inicios) - 1:
                    raise

        if os.path.exists(trecho_preview_mp4) and os.path.getsize(trecho_preview_mp4) > 0:
            print(f"✅ [Preview Isolado] Gerado com sucesso: {nome_arquivo}")
            os.replace(trecho_preview_mp4, os.path.join(PASTA_TEMP, nome_arquivo))
            return True
            
        if ao_falhar:
            ao_falhar(tr('preview.nao_gerado'))
        return False
    except Exception as e:
        print(f"⚠️ Erro ao gerar preview isolado: {e}")
        if ao_falhar:
            ao_falhar(str(e))
        return False
