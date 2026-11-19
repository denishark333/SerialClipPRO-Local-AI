import os
import json
import time
import threading
import tempfile
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = (Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "Serial ClipPRO"
                    if getattr(sys, "frozen", False) else BASE_DIR)
DATA_DIR = Path(os.environ.get("CLIPPRO_DATA_DIR", str(DEFAULT_DATA_DIR))).resolve()
# Instalacao por usuario: dispensa editar PATH ou reabrir o terminal.
if os.name == 'nt':
    caminhos = [DATA_DIR / 'tools' / 'ffmpeg',
                Path(os.getenv('LOCALAPPDATA', str(Path.home()))) / 'Programs' / 'Ollama']
    os.environ['PATH'] = os.pathsep.join([str(p) for p in caminhos if p.is_dir()] + [os.environ.get('PATH', '')])
PASTA_TEMP = str(DATA_DIR / "temp_clip_cache")
PASTA_DESTINO = str(DATA_DIR / "Cortes_Prontos")
PASTA_EXPORTADOS = str(DATA_DIR / "Cortes_Exportados")
CONFIG_LAYOUT_PATH = str(DATA_DIR / "config_layout.json")
estado_lock = threading.RLock()
config_lock = threading.RLock()

os.makedirs(PASTA_TEMP, exist_ok=True)
os.makedirs(PASTA_DESTINO, exist_ok=True)
os.makedirs(PASTA_EXPORTADOS, exist_ok=True)

estado_pipeline = {
    "status": "Idle",
    "etapa": 0,
    "progresso_pct": 0,
    "videos": [],
    "tempo_inicio": 0.0,
    "tempo_decorrido": "00:00",
    "tempo_total": "00:00"
}
estado_pipeline.update(executando=False, cancelando=False)

def carregar_config_estudio() -> dict:
    if os.path.exists(CONFIG_LAYOUT_PATH):
        try:
            with open(CONFIG_LAYOUT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "modo_estudio_ativo": False,
        "crop_jogo": {"w": 100, "h": 100, "x": 0, "y": 0},
        "crop_webcam": {"w": 35, "h": 35, "x": 60, "y": 55}
    }

def salvar_config_estudio(config: dict):
    with config_lock:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=DATA_DIR, suffix=".json", delete=False) as f:
            temporario = f.name
            json.dump(config, f, indent=4)
        try:
            os.replace(temporario, CONFIG_LAYOUT_PATH)
        finally:
            if os.path.exists(temporario):
                os.unlink(temporario)

def formatar_tempo(segundos: float) -> str:
    m = int(segundos // 60)
    s = int(segundos % 60)
    h = m // 60
    m = m % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def atualizar_estado(status: str, etapa: int, pct: int):
    with estado_lock:
        if estado_pipeline.get("cancelando"):
            return
        estado_pipeline["status"] = status
        estado_pipeline["etapa"] = etapa
        estado_pipeline["progresso_pct"] = pct
        if estado_pipeline["tempo_inicio"] > 0:
            decorrido = time.time() - estado_pipeline["tempo_inicio"]
            estado_pipeline["tempo_decorrido"] = formatar_tempo(decorrido)
