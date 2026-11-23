"""VODs da Kick quando a API usada pelo yt-dlp não encontra o vídeo.

VODs com o identificador novo (UUID v7, como kick.com/canal/videos/01a1f13a-…)
não existem em /api/v1/video, que o yt-dlp consulta. A própria página do VOD
traz a playlist HLS na metatag og:video. A Kick só entrega a página a quem se
apresenta como navegador, por isso a busca usa o curl_cffi.
"""
import html
import re
from core.textos import tr
from urllib.parse import urljoin

RE_VOD = re.compile(r'^https?://(?:www\.)?kick\.com/[\w-]+/videos/[\w-]+/?(?:[?#].*)?$')
RE_OG_VIDEO = re.compile(r'<meta[^>]+property="og:video"[^>]+content="(https://[^"]+\.m3u8[^"]*)"')


def eh_vod_kick(url):
    return bool(RE_VOD.match(url.strip()))


def _buscar(url):
    try:
        from curl_cffi import requests
    except ImportError as erro:
        raise ValueError(tr('link.kick_curl')) from erro
    resposta = requests.get(url, impersonate='chrome', timeout=30)
    resposta.raise_for_status()
    return resposta.text


def variantes(master, url_master):
    """[(banda, url, tem_audio)] de uma playlist HLS mestre."""
    linhas = master.splitlines()
    saida = []
    for i, linha in enumerate(linhas):
        if not linha.startswith('#EXT-X-STREAM-INF') or i + 1 >= len(linhas):
            continue
        banda = re.search(r'BANDWIDTH=(\d+)', linha)
        codecs = re.search(r'CODECS="([^"]*)"', linha)
        saida.append((int(banda.group(1)) if banda else 0, urljoin(url_master, linhas[i + 1].strip()),
                      not codecs or 'mp4a' in codecs.group(1)))
    return saida


def fontes_pela_pagina(url, buscar=None):
    """(áudio, vídeo) de um VOD da Kick a partir da página do vídeo.

    Sem variante só de áudio, a análise usa a menor qualidade (mesmo áudio,
    dezenas de vezes menos dados); os cortes usam a maior.
    """
    buscar = buscar or _buscar
    achado = RE_OG_VIDEO.search(buscar(url))
    if not achado:
        raise ValueError(tr('link.kick_sem_video'))
    master = html.unescape(achado.group(1))
    opcoes = variantes(buscar(master), master)
    if not opcoes:
        return master, master
    video = max(opcoes)[1]
    com_audio = [o for o in opcoes if o[2]]
    audio = min(com_audio)[1] if com_audio else video
    return audio, video
