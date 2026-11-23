"""Idioma da interface, escolhido no seletor do cabeçalho (ou pelo instalador).

É diferente do idioma da live (core/idiomas.py), que diz ao Whisper a língua
falada no vídeo. Enquanto ninguém escolheu, vale o idioma do sistema: português
abre em português e qualquer outro idioma abre em inglês.
"""
import json
import locale
import os
import threading
import uuid
from typing import Literal, Optional

from pydantic import BaseModel

from core.config import DATA_DIR

IDIOMAS = ("pt-BR", "en")
CONFIG_PATH = DATA_DIR / "config_interface.json"
_lock = threading.Lock()


class ConfigInterface(BaseModel):
    idioma: Literal["pt-BR", "en"]


def idioma_do_sistema():
    """pt-BR se o sistema estiver em português (de qualquer país), senão en."""
    codigo = ""
    if os.name == "nt":
        try:
            import ctypes
            # LANGID do idioma da interface do Windows; os 10 bits baixos são o idioma (0x16 = português).
            if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x16:
                return "pt-BR"
            return "en"
        except (AttributeError, OSError):
            pass
    for variavel in ("LC_ALL", "LC_MESSAGES", "LANG"):
        codigo = os.environ.get(variavel, "")
        if codigo:
            break
    if not codigo:
        codigo = (locale.getlocale()[0] or "")
    return "pt-BR" if codigo.lower().startswith(("pt", "portuguese")) else "en"


def salvo() -> Optional[str]:
    """Idioma escolhido pelo usuário, ou None se ainda não houve escolha."""
    with _lock:
        try:
            return ConfigInterface.model_validate_json(CONFIG_PATH.read_text(encoding="utf-8")).idioma
        except (OSError, ValueError):
            return None


def idioma():
    """Idioma em uso: o escolhido ou, sem escolha, o do sistema."""
    return salvo() or idioma_do_sistema()


def salvar(config: ConfigInterface):
    with _lock:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporario = CONFIG_PATH.with_name(CONFIG_PATH.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            temporario.write_text(json.dumps(config.model_dump()), encoding="utf-8")
            os.replace(temporario, CONFIG_PATH)
        finally:
            temporario.unlink(missing_ok=True)
    return config
