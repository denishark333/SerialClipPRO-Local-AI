import httpx
from fastapi import APIRouter, HTTPException

from core import ia
from core.textos import tr

router = APIRouter(prefix='/ia')
ORDEM_PERFIL = {'Recomendado': 0, 'Leve': 1, 'Intermediário': 2, 'Experimental': 3}


@router.get('')
def obter():
    """Modelo configurado e modelos instalados no Ollama local."""
    atual = ia.carregar().modelo
    try:
        instalados, online = ia.modelos_instalados(), True
    except (httpx.HTTPError, ValueError):
        instalados, online = [], False
    memoria = ia.memoria_gpu_gb()
    correspondente = next((m['nome'] for m in instalados if ia.mesmo_modelo(m['nome'], atual)), None)
    return {'modelo': atual, 'modelo_id': correspondente or atual, 'padrao': ia.PADRAO, 'ollama_online': online,
            'memoria_gpu_gb': memoria,
            'instalados': sorted((ia.descrever(m, memoria) for m in instalados),
                                 key=lambda m: (ORDEM_PERFIL.get(m['perfil_id'], len(ORDEM_PERFIL)), m['nome'])),
            'modelo_instalado': correspondente is not None}


@router.put('')
def salvar(config: ia.ConfigIA):
    try:
        instalados = ia.modelos_instalados()
    except (httpx.HTTPError, ValueError) as erro:
        raise HTTPException(503, tr('ollama.offline_escolha')) from erro
    if not any(ia.mesmo_modelo(m['nome'], config.modelo) for m in instalados):
        raise HTTPException(422, tr('ollama.nao_instalado', modelo=config.modelo))
    ia.salvar(config)
    return obter()
