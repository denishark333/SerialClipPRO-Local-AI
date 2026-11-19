"""Carrega o Whisper na GPU quando ela realmente funciona; senão, na CPU.

Três detalhes evitam falhas que só apareceriam no meio de uma VOD longa:

- As bibliotecas CUDA instaladas por pip (nvidia-cublas-cu12,
  nvidia-cudnn-cu12) ficam em site-packages/nvidia/*/bin, fora do caminho
  de busca de DLLs do Windows. Elas são registradas antes de carregar o modelo.
- A precisão vem do que o CTranslate2 diz que a placa suporta, não de um
  palpite pelo modelo da GPU.
- Carregar o modelo na GPU não prova que ela funciona: a falta de cuDNN só
  aparece na primeira inferência. Por isso o modelo transcreve 1 s de silêncio
  antes de ser aceito.

Qualquer falha na GPU volta para CPU/int8. A escolha vale para a sessão.

Adaptado de autoclip/cuda.py e autoclip/system.py (AutoClip, MIT, Jad Ghazi).
Veja THIRD_PARTY_LICENSES.md.
"""
import os
import sys
import threading
from pathlib import Path

MODELO = "small"
_PRECISOES_GPU = ("float16", "int8_float16", "int8")

_lock = threading.Lock()
_escolha = None  # (device, compute_type) depois da primeira carga
_dlls_registradas = False
_diretorios_dll = []  # mantém os registros de DLL vivos durante a sessão


def dispositivo():
    """Rótulo curto para mensagens de status: 'GPU' ou 'CPU'."""
    return "GPU" if _escolha and _escolha[0] == "cuda" else "CPU"


def carregar_modelo():
    """Devolve um WhisperModel pronto, na GPU quando possível."""
    global _escolha
    from faster_whisper import WhisperModel

    with _lock:
        if _escolha is None:
            modelo, escolha = _primeira_carga(WhisperModel)
            _escolha = escolha
            print(f"[Whisper] {MODELO.capitalize()} em {escolha[0].upper()}/{escolha[1]}. "
                  "O primeiro uso pode baixar o modelo.", flush=True)
            return modelo
        device, precisao = _escolha
    return WhisperModel(MODELO, device=device, compute_type=precisao)


def redefinir():
    """Esquece a escolha feita. Usado pelos testes."""
    global _escolha
    with _lock:
        _escolha = None


def _primeira_carga(WhisperModel):
    precisao = _precisao_gpu()
    if precisao:
        try:
            import numpy as np
            modelo = WhisperModel(MODELO, device="cuda", compute_type=precisao)
            segmentos, _ = modelo.transcribe(np.zeros(16000, dtype=np.float32), language="pt")
            list(segmentos)
            return modelo, ("cuda", precisao)
        except Exception as erro:
            print(f"[Whisper] GPU indisponível ({erro}). Usando CPU.", flush=True)
    return WhisperModel(MODELO, device="cpu", compute_type="int8"), ("cpu", "int8")


def _precisao_gpu():
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() < 1:
            return None
        _registrar_dlls_cuda()
        suportadas = ctranslate2.get_supported_compute_types("cuda")
    except Exception:
        return None
    return next((p for p in _PRECISOES_GPU if p in suportadas), None)


def pasta_cuda_instalada():
    """Onde o instalador coloca o cuBLAS quando a aceleração NVIDIA é escolhida.

    O pacote do CTranslate2 já traz o cuDNN; do CUDA, o Whisper só precisa de
    cublas64_12.dll e cublasLt64_12.dll, que não vão no app para manter o
    instalador leve.
    """
    from core.config import DATA_DIR
    return DATA_DIR / "tools" / "cuda"


def _registrar_pasta(pasta):
    try:
        _diretorios_dll.append(os.add_dll_directory(str(pasta)))
    except OSError:
        return
    if str(pasta) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(pasta) + os.pathsep + os.environ.get("PATH", "")


def _registrar_dlls_cuda():
    """Torna carregáveis as DLLs da NVIDIA (pip no desenvolvimento, pasta de dados no app instalado)."""
    global _dlls_registradas
    if _dlls_registradas or sys.platform != "win32":
        return
    _dlls_registradas = True
    raizes = [Path(p) / "nvidia" for p in sys.path if p]
    if getattr(sys, "frozen", False):
        raizes.append(Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "nvidia")
    for raiz in raizes:
        if not raiz.is_dir():
            continue
        for pasta in sorted(raiz.glob("*/bin")):
            _registrar_pasta(pasta)
        break
    instalada = pasta_cuda_instalada()
    if (instalada / "cublas64_12.dll").is_file():
        _registrar_pasta(instalada)
