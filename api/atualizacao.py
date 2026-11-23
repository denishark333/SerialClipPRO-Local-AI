from fastapi import APIRouter, HTTPException

from core import atualizacao
from core.textos import tr

router = APIRouter(prefix='/atualizacao')


def _sem_internos(info):
    return {chave: valor for chave, valor in info.items() if not chave.startswith('_')}


@router.get('/verificar')
def verificar():
    try:
        return _sem_internos(atualizacao.verificar())
    except RuntimeError as erro:
        raise HTTPException(502, str(erro))


@router.get('/status')
def status():
    return atualizacao.estado()


@router.post('/baixar')
def baixar():
    try:
        atualizacao.baixar()
    except RuntimeError as erro:
        raise HTTPException(502, str(erro))
    except ValueError as erro:
        raise HTTPException(409, str(erro))
    return atualizacao.estado()


@router.post('/cancelar')
def cancelar():
    atualizacao.cancelar()
    return atualizacao.estado()


@router.post('/instalar')
def instalar():
    from api.routes import preview_lock, previews_ativos
    with preview_lock:
        if previews_ativos:
            raise HTTPException(409, tr('atualizacao.aguarde'))
    try:
        atualizacao.instalar()
    except ValueError as erro:
        raise HTTPException(409, str(erro))
    return {'mensagem': tr('atualizacao.instalando')}
