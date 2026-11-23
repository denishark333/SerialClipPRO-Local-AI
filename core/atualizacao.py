"""Atualização pelo próprio app, sempre por escolha do usuário.

Fluxo: ``verificar()`` consulta a última Release no GitHub; ``baixar()`` traz o
instalador para ``<dados>/atualizacao`` e só o aceita com a assinatura Ed25519
válida; ``instalar()`` agenda o instalador para depois que o app fechar.

A assinatura cobre a versão, o nome do arquivo e o SHA-256 do instalador, com a
chave privada que fica só com o mantenedor (scripts/chave_atualizacao.py). Sem
ela, quem trocasse os arquivos da Release não conseguiria fazer o app executar
outro instalador, nem servir um instalador antigo assinado como se fosse novo.
"""
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

from core.config import DATA_DIR
from core.textos import tr
from core.version import APP_VERSION

REPOSITORIO = 'denishark333/SerialClipPRO-Local-AI'
URL_ULTIMA = f'https://api.github.com/repos/{REPOSITORIO}/releases/latest'
URL_RELEASES = f'https://github.com/{REPOSITORIO}/releases'
# Chave pública que confere os instaladores. A privada correspondente nunca entra no repositório.
CHAVE_PUBLICA = 'P6fvi1HXy+r1zngekJ//QnuykBCJNg4ex0Kjdj8mCs8='
PASTA = DATA_DIR / 'atualizacao'
TIMEOUT = 20

_lock = threading.Lock()
_estado = {'fase': 'ocioso'}
_cancelar = threading.Event()
_fechar_app = None


def versao_tupla(texto):
    """'v3.1.0' -> (3, 1, 0); None se não for uma versão numérica."""
    achado = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', str(texto).strip())
    return tuple(int(parte) for parte in achado.groups()) if achado else None


def nome_instalador(versao):
    return f'Serial-ClipPRO-{versao}-Setup-x64.exe'


def mensagem_assinada(versao, nome, sha256):
    """Bytes assinados para um instalador; o app e o script de build montam igual."""
    return f'SerialClipPRO-instalador-v1\n{versao}\n{nome}\n{sha256.lower()}\n'.encode('utf-8')


def assinatura_valida(versao, nome, sha256, assinatura_b64, chave_publica=None):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    try:
        chave = Ed25519PublicKey.from_public_bytes(base64.b64decode(chave_publica or CHAVE_PUBLICA))
        chave.verify(base64.b64decode(assinatura_b64.strip(), validate=True), mensagem_assinada(versao, nome, sha256))
        return True
    except (InvalidSignature, ValueError):
        return False


def pode_instalar():
    """Só o app instalado se atualiza; rodando pelo código, o botão leva à página de Releases."""
    return bool(getattr(sys, 'frozen', False)) and os.name == 'nt'


def _abrir(url):
    pedido = urllib.request.Request(url, headers={'User-Agent': f'SerialClipPRO/{APP_VERSION}',
                                                  'Accept': 'application/vnd.github+json'})
    return urllib.request.urlopen(pedido, timeout=TIMEOUT)


def verificar():
    """Compara a versão instalada com a última Release publicada."""
    try:
        with _abrir(URL_ULTIMA) as resposta:
            release = json.load(resposta)
    except OSError as erro:
        raise RuntimeError(tr('atualizacao.sem_conexao', erro=getattr(erro, 'reason', erro)))
    except ValueError:
        raise RuntimeError(tr('atualizacao.resposta_invalida'))
    versao = str(release.get('tag_name', '')).lstrip('v')
    if versao_tupla(versao) is None:
        raise RuntimeError(tr('atualizacao.resposta_invalida'))
    nome = nome_instalador(versao)
    anexos = {a.get('name'): a for a in release.get('assets') or [] if isinstance(a, dict)}
    instalador, assinatura = anexos.get(nome), anexos.get(nome + '.sig')
    disponivel = versao_tupla(versao) > versao_tupla(APP_VERSION)
    return {
        'atual': APP_VERSION,
        'ultima': versao,
        'disponivel': disponivel,
        'notas': str(release.get('body') or '')[:20000],
        'pagina': release.get('html_url') or URL_RELEASES,
        'tamanho': instalador.get('size') if instalador else None,
        # Sem instalador assinado na Release, a atualização é manual pela página.
        'assinada': bool(instalador and assinatura),
        'pode_instalar': pode_instalar(),
        '_urls': (instalador['browser_download_url'], assinatura['browser_download_url'])
                 if instalador and assinatura else None,
    }


def estado():
    with _lock:
        return dict(_estado)


def _definir(**valores):
    with _lock:
        _estado.clear()
        _estado.update(valores)


def baixar():
    """Inicia o download em segundo plano; a interface acompanha por ``estado()``."""
    info = verificar()
    if not info['disponivel']:
        raise ValueError(tr('atualizacao.ja_atualizado'))
    if not info['_urls']:
        raise ValueError(tr('atualizacao.sem_assinatura'))
    with _lock:
        if _estado.get('fase') == 'baixando':
            raise ValueError(tr('atualizacao.ja_baixando'))
        _estado.clear()
        _estado.update(fase='baixando', versao=info['ultima'], baixado=0, total=info['tamanho'] or 0)
    _cancelar.clear()
    threading.Thread(target=_baixar, args=(info['ultima'], *info['_urls']), daemon=True).start()


def cancelar():
    _cancelar.set()


def _baixar(versao, url_instalador, url_assinatura):
    nome = nome_instalador(versao)
    parcial = PASTA / (nome + '.parcial')
    try:
        # Um instalador por vez: o download novo substitui qualquer outro deixado ali.
        shutil.rmtree(PASTA, ignore_errors=True)
        PASTA.mkdir(parents=True, exist_ok=True)
        with _abrir(url_assinatura) as resposta:
            assinatura = resposta.read(4096).decode('ascii', 'replace')
        resumo = hashlib.sha256()
        with _abrir(url_instalador) as resposta, open(parcial, 'wb') as arquivo:
            total = int(resposta.headers.get('Content-Length') or 0)
            baixado = 0
            while True:
                if _cancelar.is_set():
                    raise InterruptedError
                bloco = resposta.read(1024 * 256)
                if not bloco:
                    break
                arquivo.write(bloco)
                resumo.update(bloco)
                baixado += len(bloco)
                _definir(fase='baixando', versao=versao, baixado=baixado, total=total)
        if not assinatura_valida(versao, nome, resumo.hexdigest(), assinatura):
            raise PermissionError(tr('atualizacao.assinatura_invalida'))
        parcial.replace(PASTA / nome)
        _definir(fase='pronto', versao=versao)
    except InterruptedError:
        shutil.rmtree(PASTA, ignore_errors=True)
        _definir(fase='ocioso')
    except Exception as erro:
        # Falha, cancelamento ou assinatura errada: nada fica para trás.
        shutil.rmtree(PASTA, ignore_errors=True)
        mensagem = str(erro) if isinstance(erro, PermissionError) else tr('atualizacao.falha_download', erro=erro)
        _definir(fase='erro', erro=mensagem)


def registrar_fechamento(funcao):
    """O desktop informa como fechar a janela depois de agendar o instalador."""
    global _fechar_app
    _fechar_app = funcao


def comando_espera(pid, instalador, log):
    """PowerShell oculto que espera o app encerrar e então abre o instalador.

    Esperar o processo inteiro (e não só a janela) garante que nenhum arquivo do
    app está em uso quando o instalador começa a substituí-los.
    """
    def literal(texto):
        return "'" + str(texto).replace("'", "''") + "'"
    script = (f'Wait-Process -Id {int(pid)} -Timeout 120 -ErrorAction SilentlyContinue; '
              f'Start-Process -FilePath {literal(instalador)} -ArgumentList '
              # Start-Process não põe aspas nos argumentos; a pasta de dados tem espaço no nome.
              f"'/SILENT','/NORESTART','/ATUALIZACAO=1',{literal('/LOG=' + chr(34) + str(log) + chr(34))}")
    codificado = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    return ['powershell.exe', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden',
            '-ExecutionPolicy', 'Bypass', '-EncodedCommand', codificado]


def instalar():
    """Agenda o instalador baixado e fecha o app; o instalador reabre o app ao terminar."""
    from core.execution import operacao_em_andamento
    if not pode_instalar() or _fechar_app is None:
        raise ValueError(tr('atualizacao.so_instalado'))
    info = estado()
    if info.get('fase') != 'pronto':
        raise ValueError(tr('atualizacao.nao_baixada'))
    instalador = PASTA / nome_instalador(info['versao'])
    if not instalador.is_file():
        raise ValueError(tr('atualizacao.nao_baixada'))
    if operacao_em_andamento():
        raise ValueError(tr('atualizacao.aguarde'))
    log = DATA_DIR / 'logs' / 'atualizacao.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(comando_espera(os.getpid(), instalador, log), close_fds=True,
                     creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
    _definir(fase='instalando', versao=info['versao'])
    # A resposta HTTP sai antes de a janela fechar.
    threading.Timer(1.0, _fechar_app).start()


def limpar_pasta(tentativas=6, intervalo=10):
    """Apaga o instalador já usado. Roda ao abrir o app, em segundo plano.

    Logo depois de uma atualização, o instalador que reabriu o app pode ainda
    estar terminando; por isso tenta de novo algumas vezes.
    """
    def tarefa():
        for _ in range(tentativas):
            if estado().get('fase') in ('baixando', 'pronto', 'instalando'):
                return
            shutil.rmtree(PASTA, ignore_errors=True)
            if not PASTA.exists():
                return
            time.sleep(intervalo)
    threading.Thread(target=tarefa, daemon=True).start()
