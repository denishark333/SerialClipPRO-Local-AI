import shutil
import subprocess
import httpx
from fastapi import APIRouter
from core.config import DATA_DIR
from core.version import APP_VERSION
from core.execution import executar_comando

router = APIRouter()


@router.get('/ambiente')
def ambiente():
    checks = {}
    for command in ('ffmpeg', 'ffprobe'):
        if not shutil.which(command):
            checks[command] = 'Não encontrado no PATH'
            continue
        try:
            result = executar_comando([command, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            checks[command] = 'Disponível' if result.returncode == 0 else 'Falha ao executar'
        except (OSError, subprocess.TimeoutExpired):
            checks[command] = 'Falha ao executar'
    try:
        response = httpx.get('http://127.0.0.1:11434/api/tags', timeout=3, trust_env=False)
        response.raise_for_status()
        models = response.json().get('models', [])
        checks['ollama'] = 'Disponível'
        checks['llama3.1'] = 'Disponível' if any(m.get('name') in ('llama3.1', 'llama3.1:latest') for m in models) else 'Modelo não instalado'
    except (httpx.HTTPError, ValueError):
        checks['ollama'] = 'Servidor não respondeu'
        checks['llama3.1'] = 'Não verificado'
    return {'versao': APP_VERSION, 'dependencias': checks, 'pasta_dados': str(DATA_DIR),
            'observacao': 'Whisper Small: usa a GPU NVIDIA quando ela funciona e, senão, a CPU (int8). '
                          'O primeiro uso pode baixar o modelo.'}
