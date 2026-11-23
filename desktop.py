"""Entrada WebView2; servidor local exclusivo com dados persistentes."""
import logging
import multiprocessing
import socket
import sys
import threading
import time
import json


def run():
    import ctypes
    # O instalador verifica este mutex antes de atualizar arquivos em uso.
    ctypes.windll.kernel32.CreateMutexW.restype = ctypes.c_void_p
    desktop_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, 'SerialClipPRO.Desktop')
    if not desktop_mutex:
        raise ctypes.WinError()
    from core.config import DATA_DIR, BASE_DIR, estado_pipeline, estado_lock
    logs = DATA_DIR / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    if sys.stdout is None:
        sys.stdout = open(logs / 'desktop.log', 'a', encoding='utf-8', buffering=1)
    if sys.stderr is None:
        sys.stderr = sys.stdout
    logging.basicConfig(filename=str(logs / 'errors.log'), level=logging.INFO)
    import webview
    import uvicorn
    from core.local_server import LocalServer
    from main import app
    if not (BASE_DIR / 'frontend/dist/index.html').is_file():
        raise RuntimeError('Frontend ausente. Execute o build antes de abrir o desktop.')
    import msvcrt
    instancia = open(DATA_DIR / 'desktop.lock', 'a+b')
    instancia.seek(0)
    if not instancia.read(1):
        instancia.write(b'0')
        instancia.flush()
    instancia.seek(0)
    try:
        msvcrt.locking(instancia.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        instancia.close()
        from core.textos import tr
        raise RuntimeError(tr('desktop.ja_aberto'))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        sock.listen(128)
        port = sock.getsockname()[1]
        server = LocalServer(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning'))
        thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 30
            while not server.started:
                if not thread.is_alive() or time.monotonic() > deadline:
                    from core.textos import tr
                    raise RuntimeError(tr('desktop.servidor'))
                time.sleep(.1)
            from core.social import DesktopSocial
            window = webview.create_window('Serial ClipPRO', f'http://127.0.0.1:{port}', width=1400, height=900, min_size=(960, 640), js_api=DesktopSocial())

            def closing():
                from core.execution import operacao_em_andamento
                from core.textos import tr
                from api.routes import preview_lock, previews_ativos
                with preview_lock:
                    active = bool(previews_ativos)
                active = active or operacao_em_andamento()
                if active:
                    window.create_confirmation_dialog(tr('desktop.processando_titulo'), tr('desktop.processando_texto'))
                    return False
                return True

            window.events.closing += closing
            webview.start(gui='edgechromium', private_mode=False, storage_path=str(DATA_DIR / 'webview'))
        finally:
            server.should_exit = True
            thread.join()
            instancia.close()


def kick_disponivel():
    """O yt-dlp só acessa a Kick se passando por navegador, via curl_cffi e sua biblioteca nativa.

    Importar o módulo do yt-dlp carrega o curl_cffi de verdade e recusa versões
    que ele não aceita: confirma que o pacote compilado trouxe as duas partes.
    """
    try:
        import yt_dlp.networking._curlcffi  # noqa: F401
        from curl_cffi import requests  # noqa: F401
        return True
    except ImportError:
        return False


def self_test():
    """Verifica imports e recursos do pacote sem abrir janela nem baixar modelos."""
    from core.config import BASE_DIR, DATA_DIR
    try:
        import webview
        from webview.platforms import winforms
        from main import app
        from faster_whisper import WhisperModel
        from PIL import Image
        resultado = {'ok': True, 'frontend': (BASE_DIR / 'frontend/dist/index.html').is_file(),
                     'webview2': winforms._is_chromium(), 'rotas': len(app.routes),
                     'kick': kick_disponivel(), 'dados': str(DATA_DIR), 'recursos': str(BASE_DIR)}
        resultado['ok'] = resultado['frontend'] and resultado['webview2'] and resultado['kick']
    except Exception as error:
        import traceback
        resultado = {'ok': False, 'erro': str(error), 'traceback': traceback.format_exc()}
    (DATA_DIR / 'self-test.json').write_text(json.dumps(resultado, indent=2), encoding='utf-8')
    return 0 if resultado['ok'] else 1


def prepare_models():
    """Baixa e carrega o Whisper como o pipeline fará: GPU testada quando disponível, senão CPU.

    Com a aceleração NVIDIA instalada, confirma já na instalação que ela funciona.
    """
    from core.config import DATA_DIR
    log = DATA_DIR / 'models-setup.log'
    with log.open('a', encoding='utf-8', buffering=1) as output:
        previous = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = output
        try:
            from core import whisper
            whisper.carregar_modelo()
            device, precisao = whisper.escolha()
            resultado = {'ok': True, 'modelo': whisper.MODELO, 'device': device, 'precisao': precisao,
                         'cuda_instalada': (whisper.pasta_cuda_instalada() / 'cublas64_12.dll').is_file()}
        except Exception as error:
            import traceback
            resultado = {'ok': False, 'erro': str(error), 'traceback': traceback.format_exc()}
        finally:
            sys.stdout, sys.stderr = previous
    (DATA_DIR / 'models-setup.json').write_text(json.dumps(resultado, indent=2), encoding='utf-8')
    return 0 if resultado['ok'] else 1


if __name__ == '__main__':
    multiprocessing.freeze_support()
    if '--self-test' in sys.argv:
        sys.exit(self_test())
    if '--prepare-models' in sys.argv:
        sys.exit(prepare_models())
    try:
        run()
    except Exception as error:
        logging.exception('Falha ao abrir desktop')
        import ctypes
        try:
            from core.textos import tr
            dica = tr('desktop.reparar')
        except Exception:  # o erro pode ser justamente o app não carregar
            dica = ('Use Preparar ou reparar Serial ClipPRO no menu Iniciar para verificar dependências. '
                    'Detalhes em logs/errors.log na pasta de dados.')
        ctypes.windll.user32.MessageBoxW(None, str(error) + '\n' + dica, 'Serial ClipPRO', 0x10)
        sys.exit(1)
