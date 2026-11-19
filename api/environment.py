import shutil
import subprocess
import httpx
from fastapi import APIRouter
from core.config import DATA_DIR
from core.version import APP_VERSION
from core.execution import executar_comando
from core import ia

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
    modelo = ia.modelo()
    try:
        instalados = ia.modelos_instalados()
        checks['ollama'] = 'Disponível'
        checks[f'modelo de IA ({modelo})'] = ('Disponível' if any(ia.mesmo_modelo(m['nome'], modelo) for m in instalados)
                                              else 'Modelo não instalado')
    except (httpx.HTTPError, ValueError):
        checks['ollama'] = 'Servidor não respondeu'
        checks[f'modelo de IA ({modelo})'] = 'Não verificado'
    return {'versao': APP_VERSION, 'dependencias': checks, 'pasta_dados': str(DATA_DIR),
            'observacao': 'Whisper Small: usa a GPU NVIDIA quando ela funciona e, senão, a CPU (int8). '
                          'O primeiro uso pode baixar o modelo.'}
