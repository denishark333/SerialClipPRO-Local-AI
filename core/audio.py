import re
import subprocess
import tempfile
from pathlib import Path
from core.textos import tr
from core.execution import executar_comando
from core.erros import ErroFFmpeg


def medir_duracao(fonte, execucao=None):
    """Duração da fonte em segundos pelo ffprobe (só lê o cabeçalho/playlist), ou None."""
    try:
        resultado = executar_comando(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                      "-of", "default=noprint_wrappers=1:nokey=1", fonte],
                                     execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, timeout=60)
        duracao = float(resultado.stdout.strip().splitlines()[0])
    except (ValueError, IndexError, OSError, subprocess.SubprocessError):
        return None
    return duracao if duracao > 0 else None


def ler_progresso(arquivo):
    """Último ``out_time_us`` (em segundos) gravado pelo ``-progress`` do ffmpeg, ou None."""
    try:
        texto = Path(arquivo).read_text(encoding='utf-8', errors='replace')
    except OSError:
        return None
    valores = re.findall(r'^out_time_us=(\d+)\s*$', texto, re.MULTILINE)
    return int(valores[-1]) / 1_000_000 if valores else None


def detectar_segmentos_narrativos(url_cdn: str, chunk_size: float = 15.0, execucao=None, ignorar_inicio_segundos=600,
                                  retornar_detalhes=False, duracao=None, ao_progresso=None):
    """Picos de áudio da fonte inteira.

    Com ``duracao`` e ``ao_progresso``, informa ``ao_progresso(segundos_lidos, duracao)``
    durante a varredura, que em VODs longas leva vários minutos.
    """
    print("🎧 Mapeando blocos narrativos e de interação...")
    with tempfile.TemporaryDirectory(prefix='clippro_mapa_') as temporario:
        return _detectar(url_cdn, execucao, ignorar_inicio_segundos, retornar_detalhes, duracao, ao_progresso,
                         Path(temporario) / 'progresso.txt')


def _detectar(url_cdn, execucao, ignorar_inicio_segundos, retornar_detalhes, duracao, ao_progresso, arquivo_progresso):
    # Uma medição por segundo, inclusive durante silêncio. O astats sozinho não
    # imprime os timestamps: ametadata publica o par tempo/RMS consumido abaixo.
    filtro_audio = ('aresample=16000,asetpts=N/SR/TB,asetnsamples=n=16000:p=1,'
                    'astats=metadata=1:reset=1,'
                    'ametadata=print:key=lavfi.astats.Overall.RMS_level')
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", url_cdn,
        "-map", "0:a:0", "-vn", "-sn", "-dn",
        "-af", filtro_audio,
        "-f", "null", "-"
    ]
    monitor = None
    if duracao and ao_progresso:
        cmd[-3:-3] = ["-progress", str(arquivo_progresso)]

        def monitor(_decorrido):
            lido = ler_progresso(arquivo_progresso)
            if lido is not None:
                ao_progresso(min(lido, duracao), duracao)

    resultado = executar_comando(cmd, execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 monitor=monitor, intervalo_monitor=3)
    if resultado.returncode != 0:
        raise ErroFFmpeg(tr('ffmpeg.analisar_audio'), resultado.stderr)
    linhas = resultado.stderr.split("\n")

    mapeamento_blocos = []
    tempo_atual = None

    for linha in linhas:
        if execucao:
            execucao.verificar()
        if "pts_time:" in linha:
            try:
                partes = linha.split("pts_time:")
                if len(partes) > 1:
                    tempo_atual = float(partes[1].split()[0])
            except Exception:
                pass

        rms_match = re.search(r"RMS(?:_level| level)?\s*[:=]\s*([-+]?\d+(?:\.\d+)?)", linha, re.IGNORECASE)
        if rms_match and tempo_atual is not None:
            try:
                rms_val = float(rms_match.group(1))
                if rms_val > -54.0:
                    mapeamento_blocos.append({"tempo": tempo_atual, "energia": rms_val})
            except ValueError:
                pass

    if tempo_atual is None:
        raise RuntimeError(tr('pipeline.audio_sem_timestamps'))
    mapeamento_blocos.sort(key=lambda x: x['energia'], reverse=True)
    
    # Em vídeos menores que a abertura ignorada, analisa desde o começo.
    limite_inicio = ignorar_inicio_segundos if tempo_atual > ignorar_inicio_segundos else 0
    pontos_selecionados = []
    for bloco in mapeamento_blocos:
        t = bloco['tempo']
        if t < limite_inicio:
            continue
            
        muito_perto = False
        for p in pontos_selecionados:
            if abs(p - t) < 90.0:
                muito_perto = True
                break
        
        if not muito_perto:
            pontos_selecionados.append(t)
            
        if len(pontos_selecionados) >= 50:
            break
            
    print(f"📊 {len(pontos_selecionados)} blocos de interesse mapeados com sucesso.")
    if retornar_detalhes:
        return {"picos": sorted(pontos_selecionados), "duracao": tempo_atual+1 if linhas else 0}
    return sorted(pontos_selecionados)
