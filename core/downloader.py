import yt_dlp

def obter_url_direta_cdn(url_vod: str) -> str:
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
        info = ydl.extract_info(url_vod, download=False)
        return info.get('url') or (info.get('requested_formats')[0].get('url') if info.get('requested_formats') else info.get('formats')[-1].get('url'))