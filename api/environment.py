import shutil
import subprocess
import httpx
from fastapi import APIRouter
from core.config import DATA_DIR
from core.version import APP_VERSION
from core.execution import executar_comando
from core import ia
from core.textos import tr

router = APIRouter()


@router.get('/ambiente')
def ambiente():
    checks = {}
    for command in ('ffmpeg', 'ffprobe'):
        if not shutil.which(command):
            checks[command] = tr('ambiente.nao_encontrado')
            continue
        try:
            result = executar_comando([command, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            checks[command] = tr('ambiente.disponivel') if result.returncode == 0 else tr('ambiente.falha')
        except (OSError, subprocess.TimeoutExpired):
            checks[command] = tr('ambiente.falha')
    modelo = ia.modelo()
    try:
        instalados = ia.modelos_instalados()
        checks['ollama'] = tr('ambiente.disponivel')
        checks[tr('ambiente.modelo', modelo=modelo)] = (tr('ambiente.disponivel') if any(ia.mesmo_modelo(m['nome'], modelo) for m in instalados)
                                                        else tr('ambiente.modelo_ausente'))
    except (httpx.HTTPError, ValueError):
        checks['ollama'] = tr('ambiente.sem_resposta')
        checks[tr('ambiente.modelo', modelo=modelo)] = tr('ambiente.nao_verificado')
    return {'versao': APP_VERSION, 'dependencias': checks, 'pasta_dados': str(DATA_DIR),
            'observacao': tr('ambiente.observacao')}
