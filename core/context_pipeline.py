"""Preparação dos cortes por contexto, sem alterar a composição visual final."""
from pathlib import Path
import subprocess
import uuid
import time

from core.config import DATA_DIR, estado_pipeline, estado_lock, atualizar_estado
from core.execution import executar_comando, PipelineCancelado
from core.transcription import transcrever_completo, salvar_json
from core.curation import analisar_contexto
from core.hybrid import transcrever_hibrido
from core.curation_status import resumir_curadoria

REPORT_DIR = DATA_DIR / "relatorios_curadoria"
#: Modos que transcrevem amostras da fonte em vez da fonte inteira.
AMOSTRADOS = ("hibrido", "picos")


def preparar_cortes_contextuais(entrada, fonte_audio, fonte_video, pasta_temp, max_cortes, execucao, ignorar_inicio, termos, resolver_video=None, modo="contexto", limite_amostras=40):
    report_id = uuid.uuid4().hex + ".json"
    caminho = REPORT_DIR / report_id
    estado_pipeline["relatorio_curadoria"] = f"/api/relatorios-curadoria/{report_id}"
    relatorio = {"entrada": entrada, "estado": "transcrevendo", "selecionados": []}

    def registrar(dados):
        relatorio.update(dados)
        relatorio['modo'] = modo
        salvar_json(caminho, relatorio)

    registrar({})
    try:
        if modo in AMOSTRADOS:
            transcricao, _ = transcrever_hibrido(fonte_audio, pasta_temp, execucao, termos, ignorar_inicio,
                                                 limite_amostras, registrar, entrada=entrada, modo=modo)
            cache = str(REPORT_DIR / (report_id[:-5] + "_amostras.json"))
            salvar_json(cache, transcricao)
        else:
            transcricao, cache = transcrever_completo(fonte_audio, entrada, pasta_temp, execucao, termos)
        registrar({"transcricao": cache, "termos_jogo": termos, "estado": "analisando"})
        inicio_curadoria = time.monotonic()
        resultado = analisar_contexto(transcricao, max_cortes, execucao, ignorar_inicio, termos, registrar,
                                      usar_cache=True)
        resumo = resultado.get('resumo_curadoria') or resumir_curadoria(resultado)
        with estado_lock:
            estado_pipeline['resumo_curadoria'] = resumo
        registrar({**resultado, "estado": "extraindo", "tempo_curadoria": time.monotonic()-inicio_curadoria})
        # A análise completa pode levar horas na CPU; renova URLs temporárias de CDN.
        if resolver_video and resultado["selecionados"]:
            execucao.verificar()
            audio_separado = fonte_audio != fonte_video
            fontes = resolver_video()
            if isinstance(fontes, tuple):
                fonte_audio, fonte_video = fontes
            else:
                fonte_video = fontes
                if not audio_separado:
                    fonte_audio = fonte_video
            execucao.verificar()
        cortes = []
        inicio_extracao = time.monotonic()
        for indice, candidato in enumerate(resultado["selecionados"]):
            execucao.verificar()
            inicio, fim = candidato["inicio"], candidato["fim"]
            trecho = str(Path(pasta_temp) / f"trecho_contexto_{indice+1}.mp4")
            atualizar_estado(f"Preparando corte por contexto {indice+1}/{len(resultado['selecionados'])}...", 2, 49)
            identificacao = f"[Extração {indice+1}/{len(resultado['selecionados'])}]"
            print(f"{identificacao} Iniciando trecho {inicio:.2f}s–{fim:.2f}s (duração {fim-inicio:.2f}s).", flush=True)
            progresso = Path(pasta_temp) / f"progresso_contexto_{indice+1}.txt"
            progresso.unlink(missing_ok=True)
            ultimo = [None, time.monotonic()]
            def monitorar(decorrido):
                dados = {}
                try:
                    with progresso.open('rb') as arquivo:
                        arquivo.seek(0, 2)
                        arquivo.seek(max(0, arquivo.tell() - 8192))
                        linhas = arquivo.read().decode('utf-8', errors='replace').splitlines()
                    for linha in linhas:
                        chave, separador, valor = linha.partition('=')
                        if separador:
                            dados[chave] = valor
                except OSError:
                    pass
                sinal = (dados.get('frame'), dados.get('out_time_us'))
                if sinal != ultimo[0] and sinal != (None, None):
                    ultimo[:] = [sinal, time.monotonic()]
                sem_avanco = time.monotonic() - ultimo[1]
                detalhe = (f"vídeo processado {dados.get('out_time', '?')}; velocidade {dados.get('speed', '?')}"
                           if dados else 'aguardando o primeiro progresso do FFmpeg')
                print(f"{identificacao} {decorrido:.0f}s decorridos; {detalhe}; "
                      f"{sem_avanco:.0f}s sem novo avanço observado.", flush=True)
            cmd = ["ffmpeg", "-y", "-nostats", "-progress", str(progresso), "-ss", str(inicio), "-i", fonte_video]
            if fonte_audio != fonte_video:
                cmd += ["-ss", str(inicio), "-i", fonte_audio, "-map", "0:v:0", "-map", "1:a:0"]
            cmd += ["-t", str(fim-inicio), "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "192k", trecho]
            marco_corte = time.monotonic()
            try:
                res = executar_comando(cmd, execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       monitor=monitorar)
            except PipelineCancelado:
                print(f"{identificacao} Cancelado após {time.monotonic()-marco_corte:.1f}s.", flush=True)
                raise
            finally:
                progresso.unlink(missing_ok=True)
            if res.returncode:
                print(f"{identificacao} FFmpeg terminou com erro {res.returncode} após {time.monotonic()-marco_corte:.1f}s.", flush=True)
                raise RuntimeError("Falha ao extrair corte contextual: " + res.stderr.decode(errors="replace")[-2000:])
            print(f"{identificacao} Extração concluída em {time.monotonic()-marco_corte:.1f}s.", flush=True)
            palavras = [
                {"word": p["word"], "start": max(0, p["start"]-inicio), "end": min(fim, p["end"])-inicio}
                for p in transcricao["palavras"] if p["end"] > inicio and p["start"] < fim
                and (modo not in AMOSTRADOS or p.get("amostra") == candidato.get("amostra"))
            ]
            cortes.append({"inicio": inicio, "duracao": fim-inicio, "palavras": palavras,
                           "trecho_path": trecho, "curadoria": {**candidato, "relatorio": report_id}})
        registrar({"estado": "selecao_concluida", "tempo_extracao_video": time.monotonic()-inicio_extracao,
                   "observacao": "A renderização dos arquivos é uma etapa posterior."})
        if not cortes:
            raise ValueError("Não foi possível montar cortes a partir das falas. Consulte o relatório de curadoria.")
        return cortes
    except PipelineCancelado:
        registrar({"estado": "cancelado"})
        raise
    except Exception as erro:
        registrar({"estado": "erro", "erro": str(erro)})
        raise
