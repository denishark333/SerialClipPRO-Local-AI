import os
import time
import json
import subprocess
import tempfile
import uuid
import math
from urllib.parse import urlsplit
from faster_whisper import WhisperModel
import ollama
import yt_dlp

from core.config import (
    PASTA_TEMP, PASTA_DESTINO,
    estado_pipeline, estado_lock, atualizar_estado,
    carregar_config_estudio, formatar_tempo
)
from core.branding import snapshot as snapshot_marca, filtro_marca
from core.downloader import obter_url_direta_cdn
from core.audio import detectar_segmentos_narrativos
from core.context_pipeline import preparar_cortes_contextuais, REPORT_DIR
from core.transcription import salvar_json
from core.subtitles import filtro_legenda, escrever_legenda
from core.composition import compor_video
from core.review import guardar as guardar_base_revisao
from core.curation_status import verificar_ollama, mensagem_conclusao
from core.encoders import renderizar, ARGS_AUDIO
from core.boundaries import refinar

from core.execution import (
    executar_comando, reservar_execucao, finalizar_execucao, PipelineCancelado,
)

#: Segundos de áudio transcritos em volta de cada pico (30 s antes, 60 s depois).
JANELA_ANALISE_PICOS = 90.0


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
    
    with yt_dlp.YoutubeDL(ydl_opts_url) as ydl:
        info = ydl.extract_info(url_limpa, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        
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
        raise Exception("Não foi possível obter a URL de streaming do vídeo.")
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
            raise ValueError("Não foi possível obter uma fonte de áudio para o modo híbrido.")
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
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([url_limpa])
            
        if execucao:
            execucao.verificar()
        video_streaming_url = obter_stream_youtube(url_limpa)

        # Garante que o arquivo m4a existe com extensão correta
        if not os.path.exists(caminho_audio_local):
            for f in os.listdir(pasta_temp):
                if f.startswith("origem") and f.endswith(".m4a"):
                    caminho_audio_local = os.path.join(pasta_temp, f)
                    break

        if execucao:
            execucao.verificar()
        if not os.path.isfile(caminho_audio_local):
            raise FileNotFoundError("O áudio do YouTube não foi gerado.")
        return caminho_audio_local, video_streaming_url
    except Exception as e:
        if execucao:
            execucao.verificar()
        raise Exception(f"Falha ao preparar YouTube: {str(e)}")

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

def executar_pipeline_background(entrada: str, max_cortes: int, execucao=None, ignorar_inicio_segundos=600, modo_curadoria="picos", termos_jogo="", limite_amostras=40):
    execucao = execucao or reservar_execucao()
    if execucao is None:
        raise RuntimeError("Já existe uma execução em andamento.")
    temporarios = None
    marco_etapa = time.monotonic()
    etapa_medida = "preparacao_origem"
    tempos = {}
    detalhes = {}
    relatorio_picos = None
    try:
        execucao.verificar()
        temporarios = tempfile.TemporaryDirectory(prefix="pipeline_", dir=PASTA_TEMP)
        pasta_temp = temporarios.name
        marca = snapshot_marca(pasta_temp)
        config_estudio = carregar_config_estudio()
        print('[Marca] ' + ('Ativa nesta execução.' if marca else 'Desativada ou sem imagem nesta execução.'))
        entrada = entrada.strip().strip('"').strip("'")
        if not entrada or not 1 <= max_cortes <= 50:
            raise ValueError("Informe uma entrada e um limite de 1 a 50 cortes.")
        atualizar_estado('Verificando Ollama e modelo llama3.1...', 1, 1)
        verificar_ollama(execucao)
        print('[Curadoria] Ollama respondeu e llama3.1 está instalado. Iniciando preparação da mídia.')
        # Rascunhos existentes permanecem disponíveis até exclusão explícita.
        # -------------------------------------------------------------
        # PASSO 1: Obtenção inteligente (Áudio leve para YT / CDN / Local)
        # -------------------------------------------------------------
        atualizar_estado("Passo 1/3: Preparando fontes de mídia...", 1, 10)
        
        audio_analise_path = None
        video_corte_fonte = None

        if entrada.startswith("http://") or entrada.startswith("https://"):
            if "youtube.com" in entrada or "youtu.be" in entrada:
                if modo_curadoria == "hibrido":
                    audio_analise_path, video_corte_fonte = obter_stream_youtube(limpar_url_youtube(entrada), incluir_audio=True)
                else:
                    audio_analise_path, video_corte_fonte = preparar_origem_youtube(entrada, pasta_temp, execucao)
                print("✅ Fontes de áudio e vídeo do YouTube preparadas.")
            else:
                video_corte_fonte = obter_url_direta_cdn(entrada)
                audio_analise_path = video_corte_fonte
                print("✅ Link CDN da Twitch/Kick obtido com sucesso.")
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
                raise FileNotFoundError(f"Ficheiro de vídeo local não encontrado: {entrada}")

        orig_w, orig_h = obter_dimensoes_video(video_corte_fonte, execucao)
        print(f"📺 Resolução de origem detectada pelo pipeline: {orig_w}x{orig_h}")

        # -------------------------------------------------------------
        # PASSO 2: Mapeamento Inteligente, Transcrição e Curadoria
        # -------------------------------------------------------------
        atualizar_estado("Passo 2/3: Analisando contexto de diálogos e reações...", 2, 30)
        
        tempos[etapa_medida] = time.monotonic() - marco_etapa
        marco_etapa = time.monotonic()
        etapa_medida = "analise_e_extracao"
        if modo_curadoria in ("contexto", "hibrido"):
            resolver_video = None
            if entrada.startswith(("http://", "https://")):
                if "youtube.com" in entrada or "youtu.be" in entrada:
                    resolver_video = lambda: obter_stream_youtube(limpar_url_youtube(entrada), incluir_audio=modo_curadoria == "hibrido")
                else:
                    resolver_video = lambda: obter_url_direta_cdn(entrada)
            cortes_validados = preparar_cortes_contextuais(
                entrada, audio_analise_path, video_corte_fonte, pasta_temp,
                max_cortes, execucao, ignorar_inicio_segundos, termos_jogo, resolver_video=resolver_video,
                modo=modo_curadoria, limite_amostras=limite_amostras,
            )
        elif modo_curadoria == "picos":
            relatorio_picos = REPORT_DIR / (uuid.uuid4().hex + ".json")
            estado_pipeline["relatorio_curadoria"] = f"/api/relatorios-curadoria/{relatorio_picos.name}"
            atualizar_estado("Picos: varrendo áudio da fonte...", 2, 15)
            inicio_subetapa = time.monotonic()
            candidatos_picos = detectar_segmentos_narrativos(audio_analise_path, execucao=execucao, ignorar_inicio_segundos=ignorar_inicio_segundos)
            detalhes["varredura_audio"] = time.monotonic() - inicio_subetapa
            detalhes["candidatos"] = len(candidatos_picos)
            execucao.verificar()
            if not candidatos_picos:
                raise ValueError("Nenhum candidato encontrado na análise de áudio.")
            inicio_subetapa = time.monotonic()
            print('[Whisper] Carregando Small (CPU/int8). O primeiro uso pode baixar o modelo.', flush=True)
            modelo_whisper = WhisperModel("small", device="cpu", compute_type="int8")
        
            detalhes["carregamento_whisper"] = time.monotonic() - inicio_subetapa
            cortes_validados = []
        
            for i, centro in enumerate(candidatos_picos):
                execucao.verificar()
                if len(cortes_validados) >= max_cortes:
                    break
                
                # Só o áudio de uma janela com folga em volta do pico: transcrever
                # não exige vídeo, e a folga deixa o ajuste encontrar frases inteiras.
                inicio_analise = max(0.0, centro - 30.0)
                audio_path = os.path.join(pasta_temp, f"audio_pico_{i+1}.wav")
                atualizar_estado(f"Picos: extraindo áudio do candidato {i+1}/{len(candidatos_picos)}...", 2, 25)
                inicio_subetapa = time.monotonic()
                resultado_audio = executar_comando([
                    "ffmpeg", "-y", "-ss", str(inicio_analise), "-i", audio_analise_path,
                    "-t", str(JANELA_ANALISE_PICOS), "-vn", "-map", "0:a:0",
                    "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", audio_path,
                ], execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                detalhes["extracao_audio"] = detalhes.get("extracao_audio", 0) + time.monotonic() - inicio_subetapa
                if resultado_audio.returncode != 0:
                    raise RuntimeError("Falha ao extrair áudio do trecho: " + resultado_audio.stderr.decode(errors="replace")[-2000:])
                if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                    continue

                palavras_analise = []
                atualizar_estado(f"Picos: transcrevendo candidato {i+1}/{len(candidatos_picos)} (CPU)...", 2, 35)
                inicio_subetapa = time.monotonic()
                try:
                    segmentos_iter, _ = modelo_whisper.transcribe(audio_path, word_timestamps=True, language="pt")
                    for seg in segmentos_iter:
                        execucao.verificar()
                        for w in getattr(seg, 'words', None) or []:
                            texto = (getattr(w, 'word', '') or '').strip()
                            if texto:
                                palavras_analise.append({"word": texto, "start": inicio_analise + float(w.start),
                                                         "end": inicio_analise + float(w.end)})
                except PipelineCancelado:
                    raise
                except Exception as e:
                    execucao.verificar()
                    print(f"⚠️ Aviso na transcrição do trecho {i+1}: {e}")
                finally:
                    if os.path.exists(audio_path):
                        os.unlink(audio_path)
                detalhes["transcricao"] = detalhes.get("transcricao", 0) + time.monotonic() - inicio_subetapa

                # Sugestão original (20 s antes e 40 s depois do pico), ajustada
                # a frases completas e pausas. Sem fala aproveitável, fica a original.
                inicio_sugerido = max(0.0, centro - 20.0)
                ajuste = refinar(palavras_analise, inicio_sugerido, inicio_sugerido + 60.0, minimo=15.0, maximo=90.0)
                inicio_janela, fim_janela = ajuste or (inicio_sugerido, inicio_sugerido + 60.0)
                duracao_janela = fim_janela - inicio_janela
                detalhes["limites_ajustados"] = detalhes.get("limites_ajustados", 0) + bool(ajuste)
                palavras_trecho = [
                    {"word": p["word"], "start": max(0.0, p["start"] - inicio_janela),
                     "end": min(p["end"], fim_janela) - inicio_janela}
                    for p in palavras_analise if p["end"] > inicio_janela and p["start"] < fim_janela
                ]
                texto_trecho = " ".join(p["word"] for p in palavras_trecho)
                system_prompt = (
                    "You are an AI video clipping assistant. Your job is to analyze stream/video transcripts. "
                    "Be extremely lenient and generous. If the snippet contains commentary, streamer reactions, "
                    "conversations, laughs, or chat interactions, mark it as valid. Only reject if it is absolute dead silence, "
                    "loading screens, or completely empty noise. "
                    "Output ONLY raw JSON: {\"valido\": true} or {\"valido\": false}."
                )
            
                execucao.verificar()
                atualizar_estado(f"Picos: avaliando candidato {i+1}/{len(candidatos_picos)}...", 2, 45)
                inicio_subetapa = time.monotonic()
                valido_ia = True
                try:
                    resp = ollama.chat(
                        model='llama3.1',
                        messages=[
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': f"Transcript: {texto_trecho if texto_trecho.strip() else 'Momento de gameplay ou reação.'}"}
                        ],
                        options={'temperature': 0.1, 'num_predict': 64}
                    )
                    conteudo_ia = resp['message']['content'].strip()
                    if "```json" in conteudo_ia:
                        conteudo_ia = conteudo_ia.split("```json")[1].split("```")[0].strip()
                    elif "```" in conteudo_ia:
                        conteudo_ia = conteudo_ia.split("```")[1].split("```")[0].strip()
                
                    res_json = json.loads(conteudo_ia)
                    if res_json.get("valido") is False:
                        if len(texto_trecho.strip()) < 3 and len(palavras_trecho) == 0:
                            valido_ia = False
                except Exception as e:
                    execucao.verificar()
                    print(f"⚠️ Aviso no Llama para o trecho {i+1}: {e}")
                    detalhes['falhas_ollama'] = detalhes.get('falhas_ollama', 0) + 1

                execucao.verificar()
                detalhes["ollama"] = detalhes.get("ollama", 0) + time.monotonic() - inicio_subetapa
                if not valido_ia:
                    continue

                # O vídeo só é extraído para candidatos aprovados, já no intervalo final.
                trecho_path = os.path.join(pasta_temp, f"trecho_pico_{i+1}.mp4")
                atualizar_estado(f"Picos: extraindo vídeo do candidato {i+1}/{len(candidatos_picos)}...", 2, 45)
                inicio_subetapa = time.monotonic()
                cmd_trecho = ["ffmpeg", "-y", "-ss", str(inicio_janela), "-i", video_corte_fonte]
                if audio_analise_path != video_corte_fonte:
                    cmd_trecho += ["-ss", str(inicio_janela), "-i", audio_analise_path, "-map", "0:v:0", "-map", "1:a:0"]
                cmd_trecho += ["-t", str(duracao_janela), "-c:v", "libx264", "-preset", "ultrafast",
                               "-c:a", "aac", "-b:a", "192k", trecho_path]
                resultado_trecho = executar_comando(cmd_trecho, execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                detalhes["extracao_trechos"] = detalhes.get("extracao_trechos", 0) + time.monotonic() - inicio_subetapa
                if resultado_trecho.returncode != 0:
                    raise RuntimeError("Falha ao extrair trecho: " + resultado_trecho.stderr.decode(errors="replace")[-2000:])
                if not os.path.exists(trecho_path) or os.path.getsize(trecho_path) < 10000:
                    continue

                cortes_validados.append({
                    "inicio": inicio_janela,
                    "duracao": duracao_janela,
                    "palavras": palavras_trecho,
                    "trecho_path": trecho_path
                })

        else:
            raise ValueError("Modo de curadoria inválido.")

        total_validos = len(cortes_validados)
        if modo_curadoria == 'picos' and detalhes.get('falhas_ollama'):
            with estado_lock:
                estado_pipeline['resumo_curadoria'] = {
                    'situacao': 'parcial', 'falhas_analise': detalhes['falhas_ollama'],
                    'mensagem': 'Houve falhas na avaliação pelo Ollama. Os cortes de Picos precisam de revisão; consulte o relatório.',
                }
        print(f"🎯 Total de ganchos liberados para curadoria: {total_validos}")

        if total_validos == 0:
            raise Exception("Nenhum gancho válido encontrado na varredura.")

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
            atualizar_estado(f"Passo 3/3: Renderizando corte {idx+1} de {total_validos}...", 3, pct)
            
            output_video = os.path.abspath(os.path.join(pasta_temp, f"corte_{timestamp_sessao}_{idx+1}.mp4"))
            
            srt_param = ""
            srt_path = None
            if corte['palavras'] and len(corte['palavras']) > 0:
                srt_path = os.path.abspath(os.path.join(pasta_temp, f"legenda_corte_{idx+1}.srt"))
                try:
                    escrever_legenda(srt_path, corte['palavras'])

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

            nome_encoder, res_render = renderizar(
                lambda codec: entradas_render + map_args + codec + ARGS_AUDIO + [output_video],
                lambda comando: executar_comando(comando, execucao=execucao, stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE, text=True),
                f'[Render] Corte {idx+1}', ao_tentar=tentativa)
            with estado_lock:
                estado_pipeline['encoder_tentativa'] = None
                if nome_encoder:
                    estado_pipeline['encoder'] = nome_encoder
            if nome_encoder is None:
                raise RuntimeError(f"Falha ao renderizar corte {idx+1}: {res_render.stderr[-2000:]}")
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
        atualizar_estado(f"Erro: {str(e)}", -1, estado_pipeline["progresso_pct"])


    finally:
        tempos[etapa_medida] = time.monotonic() - marco_etapa
        estado_pipeline["tempos_etapas"] = {k: round(v, 2) for k, v in tempos.items()}
        if relatorio_picos:
            try:
                salvar_json(relatorio_picos, {"modo": "picos", "entrada": entrada, "tempos_picos": detalhes})
            except OSError as erro:
                print(f"Falha ao salvar diagnóstico de Picos: {erro}")
        relatorio_url = estado_pipeline.get("relatorio_curadoria")
        if relatorio_url:
            caminho_relatorio = REPORT_DIR / os.path.basename(relatorio_url)
            try:
                dados = json.loads(caminho_relatorio.read_text(encoding="utf-8"))
                dados.update(tempos_etapas=estado_pipeline["tempos_etapas"], videos=estado_pipeline["videos"],
                             resultado_pipeline="cancelado" if execucao.cancelamento.is_set() else estado_pipeline["status"])
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
        raise RuntimeError("O vídeo produzido não pôde ser validado: " + resultado.stderr[-1000:])
    dados = json.loads(resultado.stdout)
    tipos = {s.get("codec_type") for s in dados.get("streams", [])}
    duracao = float(dados.get("format", {}).get("duration", 0))
    exigidos = {"video", "audio"} if exigir_audio else {"video"}
    if not exigidos.issubset(tipos) or not math.isfinite(duracao) or duracao <= 0:
        raise RuntimeError("O arquivo produzido precisa conter vídeo, áudio e duração positiva.")


def eh_url_twitch(entrada: str) -> bool:
    url = urlsplit(entrada.strip())
    host = (url.hostname or "").lower()
    return url.scheme in ("http", "https") and (host == "twitch.tv" or host.endswith(".twitch.tv"))


def gerar_preview_estudio(entrada: str, nome_arquivo: str = "preview_10s.mp4"):
    with tempfile.TemporaryDirectory(prefix="preview_job_", dir=PASTA_TEMP) as pasta_temp:
        return _gerar_preview(entrada, os.path.basename(nome_arquivo), pasta_temp)


def _gerar_preview(entrada, nome_arquivo, pasta_temp):
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
                raise FileNotFoundError(f"Ficheiro não encontrado: {entrada}")

        trecho_preview_mp4 = os.path.join(pasta_temp, nome_arquivo)
        print(f"📸 [Preview Isolado] Extraindo trecho de 10 segundos para: {nome_arquivo}...")
        
        cmd_preview_10s = [
            "ffmpeg", "-y", "-ss", "00:01:00", "-i", video_corte_fonte,
            "-t", "10", "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", trecho_preview_mp4
        ]
            
        # Twitch: evita a abertura da live. Não recua para uma tela Starting Soon.
        # Outras fontes mantêm o minuto 1 e a alternativa para vídeos curtos.
        inicios = ("00:30:00",) if eh_url_twitch(entrada) else ("00:01:00", "0")
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
            
        return False
    except Exception as e:
        print(f"⚠️ Erro ao gerar preview isolado: {e}")
        return False
