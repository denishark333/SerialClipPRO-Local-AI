import threading
from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.media import MediaResponse
from pydantic import BaseModel, Field
from core import review
from core.execution import reservar_manutencao, liberar_manutencao

router = APIRouter(prefix='/revisao')
lock = threading.Lock()
estado = {'executando': False, 'erro': None}


class Grupo(BaseModel):
    start: float = Field(ge=0, allow_inf_nan=False)
    end: float = Field(gt=0, allow_inf_nan=False)
    text: str = Field(min_length=1, max_length=500, pattern=r'^[^\r\n<>\{\}]+$')


class Edicao(BaseModel):
    revisao: int = Field(ge=0)
    legendas: list[Grupo] = Field(max_length=1000)


@router.get('/status')
def status():
    with lock:
        return dict(estado)


@router.get('/clips')
def clips():
    return review.listar()


@router.get('/cache')
def cache():
    return review.estatisticas()


@router.delete('/cache')
def limpar():
    if not reservar_manutencao():
        raise HTTPException(409, 'Aguarde o pipeline ou a revisão terminar.')
    try:
        review.limpar()
        return {'mensagem': 'Bases de revisão removidas. Vídeos finais, exportados e transcrições preservados.'}
    finally:
        liberar_manutencao()


def dados(identificador):
    try:
        return review.carregar(identificador)
    except (OSError, ValueError):
        raise HTTPException(404, 'Base de revisão indisponível.')


@router.get('/clips/{identificador}')
def detalhe(identificador: str):
    return dados(identificador)


@router.get('/clips/{identificador}/original')
def original(identificador: str):
    dados(identificador)
    return MediaResponse(review.pasta(identificador)/'original.mp4', media_type='video/mp4', headers={'Cache-Control': 'no-store'})


def executar(identificador, payload):
    try:
        review.aplicar(identificador, [g.model_dump() for g in payload.legendas], payload.revisao)
    except Exception as erro:
        with lock:
            estado['erro'] = str(erro)
    finally:
        with lock:
            estado['executando'] = False
        liberar_manutencao()


@router.post('/clips/{identificador}')
def aplicar(identificador: str, payload: Edicao, tasks: BackgroundTasks):
    dados(identificador)
    if not reservar_manutencao():
        raise HTTPException(409, 'Aguarde o pipeline ou a revisão terminar.')
    with lock:
        estado.update(executando=True, erro=None, id=identificador)
    tasks.add_task(executar, identificador, payload)
    return {'mensagem': 'Revisão iniciada.'}
