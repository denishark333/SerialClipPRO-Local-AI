"""Fonte de legenda distribuída com o aplicativo; não depende das fontes do Windows."""
from core.config import BASE_DIR
import math
from pathlib import Path


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


def escrever_legenda(caminho, palavras):
    def tempo(valor):
        ms = max(0, round(valor * 1000))
        return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
    eventos = []
    for indice, grupo in enumerate(agrupar_palavras(palavras), 1):
        texto = ' '.join(p['word'] for p in grupo)
        eventos.append(f'{indice}\n{tempo(grupo[0]["start"])} --> {tempo(max(p["end"] for p in grupo))}\n{texto}\n')
    Path(caminho).write_text('\n'.join(eventos), encoding='utf-8')


def filtro_legenda(caminho):
    fontes = BASE_DIR / 'assets' / 'fonts' / 'Bangers'
    if not (fontes / 'Bangers-Regular.ttf').is_file():
        raise FileNotFoundError('Fonte Bangers ausente. Verifique os arquivos do aplicativo.')
    def escapar(valor):
        return str(valor).replace('\\', '/').replace(':', '\\:').replace("'", "'\\\\\\''")
    return (f",subtitles=filename='{escapar(caminho)}':fontsdir='{escapar(fontes)}':"
            "force_style='FontName=Bangers,FontSize=24,PrimaryColour=&H00FFFF&,Outline=2.5,Shadow=1'")
