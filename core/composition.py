"""Composição vertical com áreas independentes de webcam e conteúdo."""
import math


def retangulo(box, largura, altura):
    valores = [float(box.get(k, v)) for k, v in [('w', 100), ('h', 100), ('x', 0), ('y', 0)]]
    w, h, x, y = valores
    if w > 100 or h > 100:  # Presets antigos em pixels de uma fonte 1920x1080.
        w, h, x, y = w/1920*100, h/1080*100, x/1920*100, y/1080*100
    x = max(0, min(int(x/100*largura) & ~1, (largura-2) & ~1))
    y = max(0, min(int(y/100*altura) & ~1, (altura-2) & ~1))
    w = max(2, min(int(w/100*largura) & ~1, (largura-x) & ~1))
    h = max(2, min(int(h/100*altura) & ~1, (altura-y) & ~1))
    return w, h, x, y


def posicao_x(config):
    """Expressão do FFmpeg para o x do recorte, conforme o foco horizontal (0 a 100, padrão no centro)."""
    try:
        foco = float(config.get('foco_conteudo', 50))
    except (TypeError, ValueError):
        foco = 50.0
    if not math.isfinite(foco):
        foco = 50.0
    foco = min(100.0, max(0.0, foco))
    return f'(iw-ow)*{foco / 100:.4f}'


def compor_video(config, largura, altura, legenda=''):
    webcam = config.get('crop_webcam') or {}
    x_conteudo = posicao_x(config)
    if not config.get('modo_estudio_ativo') or webcam.get('w', 0) <= 0:
        return (f'[0:v]scale=1080:1920:force_original_aspect_ratio=increase,'
                f'crop=1080:1920:{x_conteudo}:(ih-oh)/2,setsar=1{legenda}[v_final]'), 0
    w, h, x, y = retangulo(webcam, largura, altura)
    altura_cam = max(2, min(960, round(1080*h/w/2)*2))
    restante = 1920-altura_cam
    gw, gh, gx, gy = retangulo(config.get('crop_jogo') or {}, largura, altura)
    filtro = (
        '[0:v]split=2[orig_cam][orig_jogo];'
        f'[orig_cam]crop={w}:{h}:{x}:{y},scale=1080:{altura_cam}:force_original_aspect_ratio=decrease,'
        f'pad=1080:{altura_cam}:(ow-iw)/2:(oh-ih)/2,setsar=1[cam];'
        f'[orig_jogo]crop={gw}:{gh}:{gx}:{gy},scale=1080:{restante}:force_original_aspect_ratio=increase,'
        f'crop=1080:{restante}:{x_conteudo}:(ih-oh)/2,setsar=1[jogo];'
        f'[cam][jogo]vstack=inputs=2{legenda}[v_final]'
    )
    return filtro, altura_cam
