"""Bases de revisão independentes dos temporários de cada pipeline."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from core.config import DATA_DIR, PASTA_DESTINO, PASTA_EXPORTADOS
from core.clip_order import chave_corte
from core.transcription import salvar_json
from core.subtitles import grupos_para_revisao, palavras_da_frase, escrever_ass, filtro_legenda
from core.composition import compor_video
from core.branding import filtro_marca, estilo_legenda
from core.execution import executar_comando
from core.encoders import renderizar, medir_volume, args_audio

ROOT = DATA_DIR / 'cache_revisao'


def pasta(identificador):
    if not re.fullmatch(r'[0-9a-f]{32}', identificador):
        raise ValueError('Identificador inválido.')
    destino = (ROOT / identificador).resolve()
    if destino.parent != ROOT.resolve():
        raise ValueError('Base fora do cache de revisão.')
    return destino


def guardar(corte, nome, config, marca, largura, altura, sessao):
    ROOT.mkdir(parents=True, exist_ok=True)
    tamanho = Path(corte['trecho_path']).stat().st_size
    if shutil.disk_usage(ROOT).free < tamanho + 64 * 1024 * 1024:
        raise OSError('Espaço insuficiente para preservar o original de revisão. Libere espaço e tente novamente.')
    identificador = uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='pendente_', dir=ROOT) as temporario:
        base = Path(temporario)
        shutil.copyfile(corte['trecho_path'], base / 'original.mp4')
        marca_salva = dict(marca) if marca else None
        if marca:
            shutil.copyfile(marca['arquivo'], base / 'marca.png')
            marca_salva.pop('arquivo', None)
        # O tempo de cada palavra fica guardado para a legenda animada na revisão.
        grupos = grupos_para_revisao(corte['palavras'])
        salvar_json(base / 'dados.json', dict(id=identificador, sessao=sessao, nome=nome,
            duracao=corte['duracao'], config=config, marca=marca_salva, largura=largura,
            altura=altura, legendas=grupos, revisao=0))
        # Publicação atômica: somente bases completas se tornam visíveis.
        destino = pasta(identificador)
        base.replace(destino)
    return identificador


def carregar(identificador):
    base = pasta(identificador)
    dados = json.loads((base / 'dados.json').read_text(encoding='utf-8'))
    if not (base / 'original.mp4').is_file():
        raise FileNotFoundError('Original removido do cache.')
    if Path(dados['nome']).name != dados['nome'] or '/' in dados['nome'] or '\\' in dados['nome']:
        raise ValueError('Nome de corte inválido.')
    return dados


def listar():
    bases = {}
    for arquivo in ROOT.glob('*/dados.json'):
        try:
            dados = carregar(arquivo.parent.name)
            bases[dados['nome']] = dados['id']
        except (OSError, ValueError, KeyError):
            continue
    videos = {}
    for origem, diretorio in [('salvo', PASTA_DESTINO), ('exportado', PASTA_EXPORTADOS)]:
        for arquivo in Path(diretorio).glob('*.mp4'):
            item = videos.setdefault(arquivo.name, dict(nome=arquivo.name, id=bases.get(arquivo.name), origens=[]))
            item['origens'].append(origem)
    return sorted(videos.values(), key=lambda item: chave_corte(item['nome']))


def estatisticas():
    arquivos = [p for p in ROOT.rglob('*') if p.is_file()]
    return dict(bytes=sum(p.stat().st_size for p in arquivos), bases=sum(p.name == 'dados.json' for p in arquivos))


def limpar():
    # ROOT é dedicado: não alcança transcrições, temporários, finais ou exportados.
    if ROOT.resolve() != (DATA_DIR.resolve() / 'cache_revisao') or ROOT.is_symlink():
        raise ValueError('Diretório de cache inválido.')
    if ROOT.exists():
        shutil.rmtree(ROOT)


def aplicar(identificador, legendas, revisao):
    from core.pipeline import validar_video
    dados = carregar(identificador)
    if dados['revisao'] != revisao:
        raise ValueError('A legenda mudou. Reabra o corte antes de editar.')
    anterior = 0
    for grupo in legendas:
        if grupo['start'] < anterior or grupo['end'] <= grupo['start'] or grupo['end'] > dados['duracao'] + .1:
            raise ValueError('Timestamps devem estar em ordem, sem sobreposição e dentro do corte.')
        anterior = grupo['end']
    base = pasta(identificador)
    with tempfile.TemporaryDirectory(prefix='render_', dir=base) as temporario:
        tmp = Path(temporario)
        # Frases sem alteração mantêm o tempo real de cada palavra; as editadas são estimadas.
        legendas = [{**g, 'palavras': palavras_da_frase(g, dados['legendas'])} for g in legendas]
        legenda = tmp / 'legenda.ass'
        escrever_ass(legenda, [g['palavras'] for g in legendas], estilo_legenda())
        filtro, altura = compor_video(dados['config'], dados['largura'], dados['altura'], filtro_legenda(legenda) if legendas else '')
        entradas = ['ffmpeg', '-y', '-i', str(base/'original.mp4')]
        saida = '[v_final]'
        if dados['marca']:
            entradas += ['-i', str(base/'marca.png')]
            filtro += ';' + filtro_marca(dados['marca'], altura)
            saida = '[v_marca]'
        video = tmp/'corrigido.mp4'
        audio_final = args_audio(medir_volume(base/'original.mp4', lambda comando: executar_comando(
            comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)))
        nome_encoder, resultado = renderizar(
            lambda codec: entradas + ['-filter_complex', filtro, '-map', saida, '-map', '0:a'] + codec
                          + audio_final + [str(video)],
            lambda comando: executar_comando(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                monitor=lambda t: print(f'[Revisão] Renderizando {dados["nome"]}: {t:.0f}s', flush=True)),
            '[Revisão]')
        if nome_encoder is None:
            raise RuntimeError(resultado.stderr[-2000:])
        validar_video(str(video))
        # Exportações anteriores nunca são sobrescritas.
        destino = Path(PASTA_DESTINO)/dados['nome']
        os.replace(video, destino)
        dados.update(legendas=legendas, revisao=revisao+1)
        salvar_json(base/'dados.json', dados)
