from fastapi import APIRouter
from core import social

router = APIRouter(prefix='/social')


@router.get('')
def listar():
    nomes = social.canais()
    return {'plataformas': [{'id': key, 'titulo': value[0], 'url': value[1], 'canal': nomes.get(key, '')}
                            for key, value in social.PORTAIS.items()]}


@router.put('')
def salvar(data: social.Canal):
    social.salvar(data)
    return listar()
