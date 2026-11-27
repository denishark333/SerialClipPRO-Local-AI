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


#: Cada pessoa do Modo Podcast ocupa metade do corte: 1080 x 960 (proporção 9:8).
ALTURA_PODCAST = 960
#: Padrão do plano aberto quando o Podcast ainda não tem os lados marcados (porcentagem de um
#: vídeo 16:9): as duas metades lado a lado, cada uma 9:8 com a maior altura possível.
LADOS_PADRAO = {'esquerda': {'x': 0, 'y': 10.4938, 'w': 50, 'h': 79.0123},
                'direita': {'x': 50, 'y': 10.4938, 'w': 50, 'h': 79.0123}}
#: Cada lado fica preso à sua metade do vídeo (em %), então as duas áreas nunca se sobrepõem.
LIMITES_LADO = {'esquerda': (0, 50), 'direita': (50, 100)}


def modo_podcast(config):
    """Podcast: duas pessoas empilhadas, metade do corte para cada uma."""
    return bool(config.get('modo_estudio_ativo')) and config.get('layout_estudio') == 'podcast'


def legenda_no_centro(config):
    """Legenda no meio só na tela dividida do Podcast (na emenda); no corte único ela cobriria o rosto."""
    return modo_podcast(config) and config.get('perfil_podcast') != 'centralizado'


def posicao_da_legenda(config, segmentos=None):
    """True/False para o corte inteiro, ou, com perfis por plano, uma função do instante (s)."""
    if modo_podcast(config) and segmentos:
        if len(segmentos) == 1:
            return segmentos[0][2] == 'dividido'
        return lambda instante: next((perfil for inicio, fim, perfil in segmentos if instante < fim),
                                     segmentos[-1][2]) == 'dividido'
    return legenda_no_centro(config)


def area_lado(config, lado):
    """Área salva de um lado; fora da sua metade (ou inválida) volta ao padrão."""
    box = config.get(f'crop_{lado}') or {}
    minimo, maximo = LIMITES_LADO[lado]
    try:
        x, w = float(box.get('x', -1)), float(box.get('w', 0))
        y, h = float(box.get('y', -1)), float(box.get('h', 0))
    except (TypeError, ValueError):
        return LADOS_PADRAO[lado]
    if w > 0 and h > 0 and x >= minimo - .001 and x + w <= maximo + .001 and y >= 0 and y + h <= 100.001:
        return box
    return LADOS_PADRAO[lado]


def _cadeia_dividida(config, largura, altura, entrada, saida, prefixo=''):
    """Perfil 1: os dois lados empilhados, cada um numa metade 1080 x 960."""
    ordem = ('direita', 'esquerda') if config.get('podcast_direita_em_cima') else ('esquerda', 'direita')
    partes = [f'[{entrada}]split=2[{prefixo}p0][{prefixo}p1]']
    for indice, (lado, rotulo) in enumerate(zip(ordem, ('cima', 'baixo'))):
        w, h, x, y = retangulo(area_lado(config, lado), largura, altura)
        partes.append(f'[{prefixo}p{indice}]crop={w}:{h}:{x}:{y},'
                      f'scale=1080:{ALTURA_PODCAST}:force_original_aspect_ratio=increase,'
                      f'crop=1080:{ALTURA_PODCAST},setsar=1[{prefixo}{rotulo}]')
    partes.append(f'[{prefixo}cima][{prefixo}baixo]vstack=inputs=2[{saida}]')
    return ';'.join(partes)


def _cadeia_vertical(config, entrada, saida):
    """Perfil 2 (e modo normal): um corte vertical único, na posição horizontal escolhida."""
    return (f'[{entrada}]scale=1080:1920:force_original_aspect_ratio=increase,'
            f'crop=1080:1920:{posicao_x(config)}:(ih-oh)/2,setsar=1[{saida}]')


def compor_podcast(config, largura, altura, legenda=''):
    return _cadeia_dividida(config, largura, altura, '0:v', 'v_div') + f';[v_div]null{legenda}[v_final]', ALTURA_PODCAST


def compor_vertical(config, legenda=''):
    """Um corte vertical único do vídeo inteiro, na posição horizontal escolhida."""
    return (f'[0:v]scale=1080:1920:force_original_aspect_ratio=increase,'
            f'crop=1080:1920:{posicao_x(config)}:(ih-oh)/2,setsar=1{legenda}[v_final]'), 0


def compor_planos(config, largura, altura, legenda, segmentos):
    """Podcast automático: cada trecho com o seu perfil, juntados de volta num vídeo só.

    O último trecho vai até o fim real do vídeo, para a imagem não terminar antes do áudio.
    """
    total = len(segmentos)
    partes = ['[0:v]split=' + str(total) + ''.join(f'[s{i}]' for i in range(total))]
    for i, (inicio, fim, perfil) in enumerate(segmentos):
        limite = f':end={fim:.3f}' if i < total - 1 else ''
        partes.append(f'[s{i}]trim=start={inicio:.3f}{limite},setpts=PTS-STARTPTS[t{i}]')
        partes.append(_cadeia_dividida(config, largura, altura, f't{i}', f'r{i}', f'g{i}')
                      if perfil == 'dividido' else _cadeia_vertical(config, f't{i}', f'r{i}'))
    partes.append(''.join(f'[r{i}]' for i in range(total)) + f'concat=n={total}:v=1:a=0{legenda}[v_final]')
    # Com perfis misturados não existe uma divisão fixa para a marca d'água.
    return ';'.join(partes), 0


def compor_video(config, largura, altura, legenda='', segmentos=None):
    """Filtro do corte vertical. ``segmentos`` ([(início, fim, perfil)]) vem do Podcast automático."""
    if modo_podcast(config):
        perfil = config.get('perfil_podcast')
        if segmentos:
            if len(segmentos) > 1:
                return compor_planos(config, largura, altura, legenda, segmentos)
            perfil = segmentos[0][2]
        # Perfil 2 do Podcast: corte vertical único (closes); perfil 1: tela dividida.
        if perfil == 'centralizado':
            return compor_vertical(config, legenda)
        return compor_podcast(config, largura, altura, legenda)
    webcam = config.get('crop_webcam') or {}
    x_conteudo = posicao_x(config)
    if not config.get('modo_estudio_ativo') or webcam.get('w', 0) <= 0:
        return compor_vertical(config, legenda)
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
