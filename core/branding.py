"""Marca persistente; cada execução recebe uma cópia estável do PNG."""
import io
import json
import shutil
import threading
from core.textos import tr
import uuid
from pathlib import Path

from PIL import Image
from typing import Literal

from pydantic import BaseModel, Field
from core.config import DATA_DIR

BRAND_DIR = DATA_DIR / 'marca'
lock = threading.RLock()


class MarcaConfig(BaseModel):
    ativo: bool = False
    largura_pct: float = Field(default=35, ge=5, le=80, allow_inf_nan=False)
    x_pct: float = Field(default=50, ge=0, le=100, allow_inf_nan=False)
    y_pct: float = Field(default=8, ge=0, le=100, allow_inf_nan=False)
    posicao: str = Field(default='divisao', pattern='^(divisao|manual|topo)$')
    # Fica com a marca porque também é identidade visual; vale mesmo com a logo desativada.
    estilo_legenda: Literal['destaque', 'classico'] = 'destaque'


def carregar():
    with lock:
        arquivo = BRAND_DIR / 'config.json'
        config = MarcaConfig.model_validate_json(arquivo.read_text(encoding='utf-8')) if arquivo.exists() else MarcaConfig()
        return {**config.model_dump(), 'tem_imagem': (BRAND_DIR / 'logo.png').is_file()}


def estilo_legenda():
    return carregar()['estilo_legenda']


def salvar(config):
    with lock:
        BRAND_DIR.mkdir(parents=True, exist_ok=True)
        temp = BRAND_DIR / (uuid.uuid4().hex + '.tmp')
        try:
            temp.write_text(json.dumps(config.model_dump()), encoding='utf-8')
            temp.replace(BRAND_DIR / 'config.json')
        finally:
            temp.unlink(missing_ok=True)
    return carregar()


def upload(conteudo):
    if not conteudo or len(conteudo) > 5 * 1024 * 1024:
        raise ValueError(tr('marca.png'))
    with Image.open(io.BytesIO(conteudo)) as img:
        if img.format != 'PNG' or max(img.size) > 4096 or min(img.size) < 1:
            raise ValueError(tr('marca.dimensao'))
        img.load()
        rgba = img.convert('RGBA')
    with lock:
        BRAND_DIR.mkdir(parents=True, exist_ok=True)
        temp = BRAND_DIR / (uuid.uuid4().hex + '.png')
        try:
            rgba.save(temp, format='PNG')
            temp.replace(BRAND_DIR / 'logo.png')
        finally:
            temp.unlink(missing_ok=True)
        config = MarcaConfig(**carregar())
        config.ativo = True
        salvar(config)
    return carregar()


def remover():
    with lock:
        config = MarcaConfig(**carregar())
        config.ativo = False
        salvar(config)
        (BRAND_DIR / 'logo.png').unlink(missing_ok=True)


def snapshot(pasta):
    with lock:
        config = carregar()
        if not config['ativo'] or not config['tem_imagem']:
            return None
        caminho = Path(pasta) / 'marca.png'
        shutil.copyfile(BRAND_DIR / 'logo.png', caminho)
        with Image.open(caminho) as img:
            config['aspecto'] = img.width / img.height
        return {**config, 'arquivo': str(caminho)}


#: Distância (px) da marca até o topo, na posição Topo e no Podcast.
MARGEM_TOPO_PODCAST = 48


def filtro_marca(marca, altura_webcam=0, topo=False):
    """Sobreposição da marca no corte 1080x1920.

    ``topo``: no Podcast a legenda fica no meio (tela dividida) ou embaixo (close), e a marca vai
    sempre para cima, em qualquer enquadramento, mantendo a posição horizontal escolhida.
    """
    largura = round(1080 * marca['largura_pct'] / 100)
    altura = min(1920, max(1, round(largura / marca['aspecto'])))
    largura = min(largura, max(1, round(altura * marca['aspecto'])))
    x = round((1080 - largura) * marca['x_pct'] / 100)
    if topo or marca['posicao'] == 'topo':
        y = MARGEM_TOPO_PODCAST
    else:
        y = (round(altura_webcam - altura / 2) if marca['posicao'] == 'divisao' and altura_webcam
             else round((1920 - altura) * marca['y_pct'] / 100))
    y = max(0, min(1920 - altura, y))
    return f'[1:v]format=rgba,scale={largura}:{altura}[marca];[v_final][marca]overlay={x}:{y}:eof_action=repeat[v_marca]'
