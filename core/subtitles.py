"""Legendas queimadas no corte, com a fonte Bangers distribuída com o aplicativo.

As legendas são gravadas em ASS. No estilo "destaque", a frase inteira aparece
e a palavra que está sendo falada fica maior; no "clássico", a frase aparece
inteira, como nas versões anteriores. Fonte, cor e contorno são os mesmos nos
dois estilos (definidos em ``filtro_legenda``).
"""
from core.config import BASE_DIR
from core.textos import tr
import math
from pathlib import Path

ESTILOS = ("destaque", "classico")
PADRAO = "destaque"
#: Tamanho da palavra falada no estilo destaque, em % do tamanho normal.
ESCALA_DESTAQUE = 122

# Mesma área de referência que o FFmpeg usa ao converter SRT: o tamanho da fonte
# e do contorno continua idêntico ao das legendas antigas.
CABECALHO = """[Script Info]
ScriptType: v4.00+
PlayResX: 384
PlayResY: 288
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,16,&Hffffff,&Hffffff,&H0,&H0,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def agrupar_palavras(palavras):
    """Até cinco palavras, quebrando em pausas e finais de frase; sem preencher silêncios."""
    grupos, grupo = [], []
    def fechar():
        if not grupo:
            return
        quantidade = math.ceil(len(grupo) / 5)
        tamanho, extras = divmod(len(grupo), quantidade)
        posicao = 0
        for indice in range(quantidade):
            fim = posicao + tamanho + (indice < extras)
            grupos.append(grupo[posicao:fim])
            posicao = fim
    for palavra in palavras:
        inicio, fim = float(palavra['start']), float(palavra['end'])
        texto = palavra['word'].strip()
        if not texto or not math.isfinite(inicio) or not math.isfinite(fim) or fim <= max(0, inicio):
            continue
        item = dict(start=max(0, inicio), end=fim, word=texto)
        if grupo and (inicio - grupo[-1]['end'] >= .45
                      or fim - grupo[0]['start'] > 3.5):
            fechar()
            grupo = []
        grupo.append(item)
        if texto.endswith(('.', '!', '?')):
            fechar()
            grupo = []
    if grupo:
        fechar()
    return grupos


def grupos_para_revisao(palavras):
    """Frases editáveis na revisão, guardando o tempo de cada palavra."""
    return [{'start': g[0]['start'], 'end': max(p['end'] for p in g),
             'text': ' '.join(p['word'] for p in g), 'palavras': g} for g in agrupar_palavras(palavras)]


def palavras_estimadas(grupo):
    """Tempos de cada palavra de uma frase sem marcação por palavra.

    Divide a duração da frase proporcionalmente ao tamanho de cada palavra:
    acontece em bases antigas e quando o texto é editado na revisão.
    """
    termos = grupo['text'].split()
    if not termos:
        return []
    inicio, fim = float(grupo['start']), float(grupo['end'])
    pesos = [len(t) + 1 for t in termos]
    total, acumulado, palavras = sum(pesos), 0, []
    for termo, peso in zip(termos, pesos):
        a = inicio + (fim - inicio) * acumulado / total
        acumulado += peso
        palavras.append({'start': a, 'end': inicio + (fim - inicio) * acumulado / total, 'word': termo})
    return palavras


def palavras_da_frase(grupo, anteriores=()):
    """Palavras com tempo real quando a frase não mudou; estimadas quando mudou."""
    for antigo in anteriores:
        palavras = antigo.get('palavras')
        if (palavras and antigo['text'].split() == grupo['text'].split()
                and abs(antigo['start'] - grupo['start']) < .01 and abs(antigo['end'] - grupo['end']) < .01):
            return palavras
    return palavras_estimadas(grupo)


def _tempo(valor):
    cs = max(0, round(valor * 100))
    return f'{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}'


def _limpar(texto):
    # Chaves e barra invertida são comandos no ASS; uma fala nunca deve virar formatação.
    return texto.replace('\\', '/').replace('{', '(').replace('}', ')')


def eventos(grupo, estilo):
    """(início, fim, texto ASS) de uma frase."""
    palavras = [_limpar(p['word']) for p in grupo]
    fim_frase = max(p['end'] for p in grupo)
    if estilo == 'classico':
        return [(grupo[0]['start'], fim_frase, ' '.join(palavras))]
    saida = []
    for i, palavra in enumerate(grupo):
        # Cada palavra fica destacada até a próxima começar: sem buracos na frase.
        inicio = palavra['start'] if i else grupo[0]['start']
        fim = grupo[i + 1]['start'] if i + 1 < len(grupo) else fim_frase
        if fim <= inicio:
            continue
        texto = ' '.join(
            f'{{\\fscx{ESCALA_DESTAQUE}\\fscy{ESCALA_DESTAQUE}}}{p}{{\\fscx100\\fscy100}}' if n == i else p
            for n, p in enumerate(palavras))
        saida.append((inicio, fim, texto))
    return saida


#: Estilo padrão: alinhada embaixo (2) ou no meio da tela (5), na numeração do ASS v4+.
_ESTILO_BAIXO = 'Style: Default,Arial,16,&Hffffff,&Hffffff,&H0,&H0,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,0'
_ESTILO_CENTRO = 'Style: Default,Arial,16,&Hffffff,&Hffffff,&H0,&H0,0,0,0,0,100,100,0,0,1,1,0,5,10,10,0,0'


def escrever_ass(caminho, grupos, estilo=PADRAO, centro=False):
    """Grava a legenda; ``centro`` a põe no meio da tela, na emenda do Modo Podcast.

    ``centro`` também pode ser uma função do instante (s), quando o Podcast troca de perfil
    plano a plano: cada frase fica onde pede o plano em que ela começa.
    """
    estilo = estilo if estilo in ESTILOS else PADRAO
    por_frase = callable(centro)
    cabecalho = CABECALHO.replace(_ESTILO_BAIXO, _ESTILO_CENTRO) if centro is True else CABECALHO
    linhas = []
    for grupo in grupos:
        if not grupo:
            continue
        # \an5: no meio da tela, só nesta frase (o estilo continua embaixo).
        prefixo = '{\\an5}' if por_frase and centro(grupo[0]['start']) else ''
        linhas += [f'Dialogue: 0,{_tempo(a)},{_tempo(b)},Default,,0,0,0,,{prefixo}{texto}\n'
                   for a, b, texto in eventos(grupo, estilo)]
    Path(caminho).write_text(cabecalho + ''.join(linhas), encoding='utf-8')


def escrever_legenda(caminho, palavras, estilo=PADRAO, centro=False):
    escrever_ass(caminho, agrupar_palavras(palavras), estilo, centro)


def filtro_legenda(caminho):
    fontes = BASE_DIR / 'assets' / 'fonts' / 'Bangers'
    if not (fontes / 'Bangers-Regular.ttf').is_file():
        raise FileNotFoundError(tr('pipeline.fonte_ausente'))
    def escapar(valor):
        return str(valor).replace('\\', '/').replace(':', '\\:').replace("'", "'\\\\\\''")
    return (f",subtitles=filename='{escapar(caminho)}':fontsdir='{escapar(fontes)}':"
            "force_style='FontName=Bangers,FontSize=24,PrimaryColour=&H00FFFF&,Outline=2.5,Shadow=1'")
