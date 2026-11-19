import yt_dlp


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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url_vod, download=False)


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
