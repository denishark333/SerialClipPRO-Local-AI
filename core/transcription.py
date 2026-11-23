"""Transcrição completa em blocos de áudio, com cache reutilizável."""
import hashlib
import json
from core.textos import tr
import math
import os
from pathlib import Path
import subprocess
import time
import uuid
import wave

from core.whisper import carregar_modelo, dispositivo
from core.idiomas import para_whisper
from core.config import DATA_DIR, atualizar_estado
from core.execution import executar_comando
from core.erros import ErroFFmpeg

CACHE_DIR = DATA_DIR / "transcricoes"
VERSAO = 1


def identidade_entrada(entrada):
    """URL como digitada; arquivo local por caminho, tamanho e data de modificação."""
    identidade = entrada.strip()
    if os.path.isfile(identidade):
        stat = os.stat(identidade)
        identidade = [os.path.abspath(identidade), stat.st_size, stat.st_mtime_ns]
    return identidade


def chave(*partes):
    """Identificador de cache derivado de tudo que influencia o resultado."""
    return hashlib.sha256(json.dumps(list(partes), ensure_ascii=False).encode()).hexdigest()


def ler_json(caminho):
    """Conteúdo de um cache, ou None se ausente ou corrompido."""
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def chave_transcricao(entrada, termos, idioma="pt"):
    # "cpu"/"int8" é o rótulo histórico desta configuração; mantido para não
    # invalidar caches existentes. O texto não depende do dispositivo usado.
    return chave(VERSAO, identidade_entrada(entrada), "small", "cpu", "int8", idioma, termos)


TENTATIVAS_TROCA = (0.05, 0.1, 0.2, 0.4, 0.8, 1.5)


def substituir(origem, destino):
    """``os.replace`` que tolera o arquivo aberto por outro programa.

    No Windows, o antivírus, o indexador ou um download do relatório podem
    segurar o destino por instantes, e a troca falha com "Acesso negado".
    Tenta de novo por até ~3 s antes de desistir.
    """
    for espera in TENTATIVAS_TROCA:
        try:
            os.replace(origem, destino)
            return
        except PermissionError:
            time.sleep(espera)
    os.replace(origem, destino)


def salvar_json(caminho, dados):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        substituir(temporario, caminho)
    finally:
        if temporario.exists():
            temporario.unlink()


def transcrever_completo(fonte, entrada, pasta_temp, execucao, termos="", idioma="pt"):
    execucao.verificar()
    caminho_cache = CACHE_DIR / (chave_transcricao(entrada, termos, idioma) + ".json")
    if caminho_cache.exists():
        try:
            dados = json.loads(caminho_cache.read_text(encoding="utf-8"))
            if dados["versao"] == VERSAO and dados.get("modelo") == "small" and isinstance(dados["segmentos"], list) and dados["duracao"] > 0:
                atualizar_estado(tr('status.transcricao_cache'), 2, 34)
                return dados, str(caminho_cache)
        except (ValueError, KeyError, TypeError):
            pass

    atualizar_estado(tr('status.preparando_audio'), 2, 15)
    pasta_audio = Path(pasta_temp) / "audio_contexto"
    pasta_audio.mkdir()
    resultado = executar_comando([
        "ffmpeg", "-y", "-i", fonte, "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", "-f", "segment", "-segment_time", "600", "-reset_timestamps", "1",
        str(pasta_audio / "bloco_%05d.wav"),
    ], execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if resultado.returncode:
        raise ErroFFmpeg(tr('ffmpeg.preparar_audio'), resultado.stderr)
    blocos = sorted(pasta_audio.glob("bloco_*.wav"))
    if not blocos:
        raise ValueError(tr('pipeline.sem_audio'))

    execucao.verificar()
    modelo = carregar_modelo()
    segmentos, palavras = [], []
    offset = 0.0
    for indice, bloco in enumerate(blocos):
        execucao.verificar()
        with wave.open(str(bloco), "rb") as wav:
            duracao = wav.getnframes() / wav.getframerate()
        atualizar_estado(tr('status.transcrevendo_vod', atual=indice+1, total=len(blocos), dispositivo=dispositivo()), 2, 16 + int(18 * indice / len(blocos)))
        iterator, _ = modelo.transcribe(
            str(bloco), language=para_whisper(idioma), word_timestamps=True, beam_size=5,
            vad_filter=True, hotwords=termos or None,
        )
        for seg in iterator:
            execucao.verificar()
            inicio, fim = max(0.0, float(seg.start)), min(duracao, float(seg.end))
            if not all(math.isfinite(t) for t in (inicio, fim)) or fim <= inicio or not seg.text.strip():
                continue
            segmentos.append({"id": f"s{len(segmentos)+1:06d}", "start": offset+inicio, "end": offset+fim, "text": seg.text.strip()})
            for palavra in seg.words or []:
                st, et = max(inicio, float(palavra.start)), min(fim, float(palavra.end))
                if math.isfinite(st) and math.isfinite(et) and et > st and palavra.word.strip():
                    palavras.append({"start": offset+st, "end": offset+et, "word": palavra.word.strip()})
        offset += duracao
        bloco.unlink()
    execucao.verificar()
    dados = {"versao": VERSAO, "modelo": "small", "termos": termos, "duracao": offset, "segmentos": segmentos, "palavras": palavras}
    salvar_json(caminho_cache, dados)
    return dados, str(caminho_cache)
