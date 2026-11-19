import re

import yt_dlp


MENSAGEM_LIVE = ("Esse link é de uma live em andamento (ou do canal). O Serial ClipPRO trabalha com "
                 "vídeos completos: use o link do VOD, por exemplo twitch.tv/videos/… ou "
                 "kick.com/canal/videos/…, depois que a live terminar.")


def recusar_live(info: dict) -> None:
    """Lives não têm começo fixo nem links duráveis: a varredura só ouviria os minutos
    seguintes e os trechos sumiriam da janela da transmissão antes do corte."""
    if info.get('is_live') or info.get('live_status') in ('is_live', 'is_upcoming'):
        raise ValueError(MENSAGEM_LIVE)


def extrair_info(opcoes: dict, url: str) -> dict:
    """``extract_info`` com mensagem legível quando o link não abre."""
    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            return ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as erro:
        texto = re.sub(r"\[[0-9;]*m", "", str(erro)).replace("ERROR: ", "").strip()
        if re.search(r"is (currently )?offline|not (currently )?live", texto, re.I):
            raise ValueError("O canal está offline e o link não aponta para um VOD. "
                             "Use o link do VOD (twitch.tv/videos/… ou kick.com/canal/videos/…).") from erro
        raise ValueError(f"Não foi possível abrir o link: {texto[:300]}") from erro


def _extrair(url_vod: str) -> dict:
    ydl_opts = {
        'noplaylist': True,
        'skip_download': True,
    }

    # Define o formato compatível para YouTube vs Twitch/Kick
    if "youtube.com" in url_vod or "youtu.be" in url_vod:
        ydl_opts['format'] = 'best[ext=mp4]/best'
    else:
        ydl_opts['format'] = 'best'

    info = extrair_info(ydl_opts, url_vod)
    recusar_live(info)
    return info


def _url_video(info: dict) -> str:
    return info.get('url') or (info.get('requested_formats')[0].get('url') if info.get('requested_formats') else info.get('formats')[-1].get('url'))


def obter_url_direta_cdn(url_vod: str) -> str:
    return _url_video(_extrair(url_vod))


def obter_fontes_cdn(url_vod: str) -> tuple[str, str]:
    """(áudio, vídeo) de uma VOD da Twitch/Kick, numa única consulta.

    A Twitch oferece uma variante só de áudio (audio_only). Usá-la na varredura
    e na transcrição evita baixar o vídeo em alta resolução da VOD inteira só
    para medir volume. Sem essa variante, o áudio vem do próprio vídeo.
    """
    info = _extrair(url_vod)
    video = _url_video(info)
    so_audio = [f for f in info.get('formats') or []
                if f.get('url') and f.get('vcodec') == 'none' and f.get('acodec') not in (None, 'none')]
    if not so_audio:
        return video, video
    melhor = max(so_audio, key=lambda f: f.get('abr') or f.get('tbr') or 0)
    return melhor['url'], video
