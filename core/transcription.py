"""Transcrição completa em blocos de áudio, na CPU, com cache reutilizável."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import uuid
import wave

from faster_whisper import WhisperModel
from core.config import DATA_DIR, atualizar_estado
from core.execution import executar_comando

CACHE_DIR = DATA_DIR / "transcricoes"
VERSAO = 1


def chave_transcricao(entrada, termos):
    identidade = entrada.strip()
    if os.path.isfile(identidade):
        stat = os.stat(identidade)
        identidade = [os.path.abspath(identidade), stat.st_size, stat.st_mtime_ns]
    dados = [VERSAO, identidade, "small", "cpu", "int8", "pt", termos]
    return hashlib.sha256(json.dumps(dados, ensure_ascii=False).encode()).hexdigest()


def salvar_json(caminho, dados):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        os.replace(temporario, caminho)
    finally:
        if temporario.exists():
            temporario.unlink()


def transcrever_completo(fonte, entrada, pasta_temp, execucao, termos=""):
    execucao.verificar()
    caminho_cache = CACHE_DIR / (chave_transcricao(entrada, termos) + ".json")
    if caminho_cache.exists():
        try:
            dados = json.loads(caminho_cache.read_text(encoding="utf-8"))
            if dados["versao"] == VERSAO and dados.get("modelo") == "small" and isinstance(dados["segmentos"], list) and dados["duracao"] > 0:
                atualizar_estado("Transcrição completa recuperada do cache.", 2, 34)
                return dados, str(caminho_cache)
        except (ValueError, KeyError, TypeError):
            pass

    atualizar_estado("Preparando áudio completo para análise de contexto...", 2, 15)
    pasta_audio = Path(pasta_temp) / "audio_contexto"
    pasta_audio.mkdir()
    resultado = executar_comando([
        "ffmpeg", "-y", "-i", fonte, "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", "-f", "segment", "-segment_time", "600", "-reset_timestamps", "1",
        str(pasta_audio / "bloco_%05d.wav"),
    ], execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if resultado.returncode:
        raise RuntimeError("Falha ao preparar áudio: " + resultado.stderr.decode(errors="replace")[-2000:])
    blocos = sorted(pasta_audio.glob("bloco_*.wav"))
    if not blocos:
        raise ValueError("Nenhum áudio disponível para transcrição.")

    execucao.verificar()
    print('[Whisper] Carregando Small (CPU/int8). O primeiro uso pode baixar o modelo.', flush=True)
    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segmentos, palavras = [], []
    offset = 0.0
    for indice, bloco in enumerate(blocos):
        execucao.verificar()
        with wave.open(str(bloco), "rb") as wav:
            duracao = wav.getnframes() / wav.getframerate()
        atualizar_estado(f"Transcrevendo a VOD: bloco {indice+1}/{len(blocos)} (CPU)...", 2, 16 + int(18 * indice / len(blocos)))
        iterator, _ = modelo.transcribe(
            str(bloco), language="pt", word_timestamps=True, beam_size=5,
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
