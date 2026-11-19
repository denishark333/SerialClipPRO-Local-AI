from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from core import branding

router = APIRouter(prefix='/marca')


@router.get('')
def config():
    return branding.carregar()


@router.put('')
def salvar(data: branding.MarcaConfig):
    return branding.salvar(data)


@router.put('/imagem')
async def upload(request: Request):
    dados = bytearray()
    async for parte in request.stream():
        dados.extend(parte)
        if len(dados) > 5 * 1024 * 1024:
            raise HTTPException(413, 'O limite da imagem é 5 MB.')
    try:
        return branding.upload(bytes(dados))
    except (ValueError, UnidentifiedImageError, OSError, Image.DecompressionBombError) as erro:
        raise HTTPException(422, str(erro)) from erro


@router.get('/imagem')
def imagem():
    with branding.lock:
        caminho = branding.BRAND_DIR / 'logo.png'
        if not caminho.exists():
            raise HTTPException(404, 'Nenhuma marca enviada.')
        return Response(caminho.read_bytes(), media_type='image/png', headers={'Cache-Control': 'no-store'})


@router.delete('')
def remover():
    branding.remover()
    return branding.carregar()
