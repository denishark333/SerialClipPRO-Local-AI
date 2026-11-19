"""Modelo de IA local (Ollama) usado na curadoria, escolhido pelo usuário.

O padrão continua sendo o llama3.1, que o instalador baixa. Qualquer modelo
já instalado no Ollama pode ser escolhido; trocar de modelo invalida os
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
