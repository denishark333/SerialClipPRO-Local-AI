from fastapi import APIRouter

from core import interface

router = APIRouter(prefix='/interface')


@router.get('')
def obter():
    escolhido = interface.salvo()
    return {'idioma': escolhido or interface.idioma_do_sistema(), 'escolhido': escolhido is not None,
            'disponiveis': list(interface.IDIOMAS)}


@router.put('')
def salvar(config: interface.ConfigInterface):
    interface.salvar(config)
    return obter()
