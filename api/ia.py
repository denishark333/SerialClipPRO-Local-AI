import httpx
from fastapi import APIRouter, HTTPException

from core import ia

router = APIRouter(prefix='/ia')


@router.get('')
def obter():
    """Modelo configurado e modelos instalados no Ollama local."""
    atual = ia.carregar().modelo
    try:
        instalados, online = ia.modelos_instalados(), True
    except (httpx.HTTPError, ValueError):
        instalados, online = [], False
    return {'modelo': atual, 'padrao': ia.PADRAO, 'ollama_online': online, 'instalados': instalados,
            'modelo_instalado': any(ia.mesmo_modelo(m['nome'], atual) for m in instalados)}


@router.put('')
def salvar(config: ia.ConfigIA):
    try:
        instalados = ia.modelos_instalados()
    except (httpx.HTTPError, ValueError) as erro:
        raise HTTPException(503, 'O Ollama não respondeu. Abra o Ollama para escolher um modelo instalado.') from erro
    if not any(ia.mesmo_modelo(m['nome'], config.modelo) for m in instalados):
        raise HTTPException(422, f'O modelo {config.modelo} não está instalado no Ollama.')
    ia.salvar(config)
    return obter()
