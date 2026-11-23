"""Modelo de IA local (Ollama) usado na curadoria, escolhido pelo usuário.

O padrão é o llama3.1, o mais leve. O instalador baixa os modelos marcados e
grava aqui o mais forte entre eles. Qualquer modelo já instalado no Ollama pode
ser escolhido; trocar de modelo invalida os
checkpoints de curadoria automaticamente, porque o nome do modelo faz parte
da chave do cache.
"""
import json
import os
import threading
import uuid

import httpx
from pydantic import BaseModel, Field

from core.config import DATA_DIR

PADRAO = "llama3.1"
CONFIG_PATH = DATA_DIR / "config_ia.json"
URL_OLLAMA = "http://127.0.0.1:11434"
_lock = threading.Lock()


class ConfigIA(BaseModel):
    modelo: str = Field(default=PADRAO, min_length=1, max_length=200, pattern=r"^[A-Za-z0-9._:/-]+$")


def carregar():
    with _lock:
        try:
            return ConfigIA.model_validate_json(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ConfigIA()


def modelo():
    """Nome do modelo configurado para a curadoria."""
    return carregar().modelo


def salvar(config):
    with _lock:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporario = CONFIG_PATH.with_name(CONFIG_PATH.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            temporario.write_text(json.dumps(config.model_dump()), encoding="utf-8")
            os.replace(temporario, CONFIG_PATH)
        finally:
            temporario.unlink(missing_ok=True)
    return config


def mesmo_modelo(a, b):
    """'llama3.1' e 'llama3.1:latest' são o mesmo modelo no Ollama."""
    def base(nome):
        return nome if ":" in nome else nome + ":latest"
    return base(a) == base(b)


#: Modelos avaliados na curadoria (VOD real de 15 h, 40 amostras do Híbrido).
#: memoria_gb é a memória de vídeo medida com contexto de 8192 tokens.
CATALOGO = {
    "gemma4:12b": {"nome": "Gemma 4 12B", "perfil": "Recomendado",
                   "descricao": "Melhor curadoria nos testes: descreve os momentos com precisão e cita falas reais.",
                   "memoria_gb": 9.2},
    "llama3.1:latest": {"nome": "Llama 3.1 8B", "perfil": "Leve",
                        "descricao": "Funciona na maioria das placas. Encontra mais momentos, com descrições menos precisas.",
                        "memoria_gb": 5.8},
    "qwen3.5:9b": {"nome": "Qwen 3.5 9B", "perfil": "Intermediário",
                   "descricao": "Boas descrições, mas pode juntar ou alterar as falas citadas.",
                   "memoria_gb": 6.6},
    "qwen3:14b": {"nome": "Qwen 3 14B", "perfil": "Experimental",
                  "descricao": "Muito seletivo: encontrou poucos momentos nos testes.",
                  "memoria_gb": 10.3},
}


def _normalizar_nome(nome):
    return nome if ":" in nome else nome + ":latest"


#: Classe "Display adapters" do Windows: cada subchave NNNN é uma placa de vídeo.
_CLASSE_VIDEO = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
#: Fabricantes cujas placas o Ollama usa no Windows. Intel e placas virtuais ficam de fora.
_FABRICANTES_OLLAMA = ("nvidia", "advanced micro devices", "amd")


def memoria_gpu_gb(timeout=5):
    """Memória da maior GPU NVIDIA ou AMD em GB, ou None se não houver ou não der para medir."""
    return _memoria_nvidia_smi(timeout) or _memoria_registro()


def _memoria_nvidia_smi(timeout):
    import shutil
    import subprocess
    if not shutil.which("nvidia-smi"):
        return None
    try:
        saida = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                               capture_output=True, text=True, timeout=timeout,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return round(max(float(linha) for linha in saida.stdout.split() if linha.strip()) / 1024, 1)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _memoria_registro():
    """Memória dedicada informada pelo driver no registro do Windows (vale para AMD sem nvidia-smi).

    O valor de 64 bits (qwMemorySize) é o confiável: o de 32 bits e o AdapterRAM
    do WMI param em 4 GB.
    """
    try:
        import winreg
    except ImportError:  # Linux/Colab: lá vale só o nvidia-smi.
        return None
    maior = 0
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _CLASSE_VIDEO) as classe:
            indice = 0
            while True:
                try:
                    nome = winreg.EnumKey(classe, indice)
                except OSError:
                    break
                indice += 1
                if not nome.isdigit():
                    continue
                try:
                    with winreg.OpenKey(classe, nome) as placa:
                        fabricante = str(winreg.QueryValueEx(placa, "ProviderName")[0]).lower()
                        memoria = int(winreg.QueryValueEx(placa, "HardwareInformation.qwMemorySize")[0])
                except (OSError, ValueError, TypeError):
                    continue
                if fabricante.startswith(_FABRICANTES_OLLAMA):
                    maior = max(maior, memoria)
    except OSError:
        return None
    return round(maior / 1024 ** 3, 1) if maior else None


def descrever(modelo, memoria_gpu=None):
    """Acrescenta nome amigável, perfil e se cabe na GPU a um item de modelos_instalados()."""
    info = CATALOGO.get(_normalizar_nome(modelo["nome"]))
    if info:
        item = {**modelo, **info}
    else:
        item = {**modelo, "nome": modelo["nome"], "perfil": "", "memoria_gb": None,
                "descricao": "Modelo não avaliado no ClipPRO; os resultados podem variar."}
    item["id"] = modelo["nome"]
    # Margem de ~1 GB para o sistema e o Whisper; sem GPU detectada, não opina.
    item["cabe_na_gpu"] = (None if memoria_gpu is None or item["memoria_gb"] is None
                           else item["memoria_gb"] <= memoria_gpu - 1)
    return item


def modelos_instalados(timeout=3):
    """Modelos do Ollama local, com tamanho e parâmetros. Levanta httpx.HTTPError se offline."""
    resposta = httpx.get(f"{URL_OLLAMA}/api/tags", timeout=timeout, trust_env=False)
    resposta.raise_for_status()
    modelos = []
    for item in resposta.json().get("models", []):
        detalhes = item.get("details") or {}
        modelos.append({
            "nome": item.get("name", ""),
            "tamanho_gb": round((item.get("size") or 0) / 1e9, 1),
            "parametros": detalhes.get("parameter_size") or "",
            "quantizacao": detalhes.get("quantization_level") or "",
        })
    return sorted(modelos, key=lambda m: m["nome"])
