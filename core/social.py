"""Atalhos oficiais; não autentica nem publica em nome do usuário."""
import json
import threading
import uuid
from core.textos import tr
from typing import Literal
from pydantic import BaseModel, Field
from core.config import DATA_DIR

PORTAIS = {
    'instagram': ('Instagram', 'https://www.instagram.com/'),
    'tiktok': ('TikTok', 'https://www.tiktok.com/tiktokstudio/upload'),
    'youtube': ('YouTube / Shorts', 'https://studio.youtube.com/'),
    'twitch': ('Twitch', 'https://dashboard.twitch.tv/'),
    'kick': ('Kick', 'https://dashboard.kick.com/'),
}
CONFIG_PATH = DATA_DIR / 'social_canais.json'
lock = threading.RLock()


class Canal(BaseModel):
    plataforma: Literal['instagram', 'tiktok', 'youtube', 'twitch', 'kick']
    nome: str = Field(default='', max_length=100)


def canais():
    with lock:
        try:
            return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}


def salvar(canal):
    with lock:
        dados = canais()
        dados[canal.plataforma] = canal.nome.strip()
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        temp = CONFIG_PATH.with_suffix('.' + uuid.uuid4().hex + '.tmp')
        try:
            temp.write_text(json.dumps(dados, ensure_ascii=False), encoding='utf-8')
            temp.replace(CONFIG_PATH)
        finally:
            temp.unlink(missing_ok=True)
        return dados


class DesktopSocial:
    def __init__(self):
        self._windows = {}
        self._lock = threading.Lock()

    def selecionar_video(self):
        import webview
        selected = webview.windows[0].create_file_dialog(
            webview.FileDialog.OPEN, allow_multiple=False,
            file_types=(f"{tr('seletor.videos')} (*.mp4;*.mkv;*.mov;*.avi;*.webm;*.m4v;*.ts;*.flv)", f"{tr('seletor.todos')} (*.*)"),
        )
        return {'caminho': selected[0] if selected else ''}

    def abrir_doacao(self, metodo):
        import webbrowser
        links = {
            'pix': 'https://livepix.gg/serialhealer',
            'paypal': 'https://www.paypal.com/donate/?business=6KXEQHVYHLLQ8&no_recurring=0&item_name=Host%2FVPS&currency_code=BRL',
        }
        if metodo not in links:
            raise ValueError(tr('social.metodo'))
        return webbrowser.open(links[metodo])

    def abrir_releases(self, url=''):
        """Página de Releases no navegador; só aceita páginas do próprio repositório."""
        import webbrowser
        from core.atualizacao import URL_RELEASES
        return webbrowser.open(url if str(url).startswith(URL_RELEASES + '/') else URL_RELEASES)

    def salvar_corte(self, nome):
        from pathlib import Path
        import shutil
        import webview
        from core.config import PASTA_DESTINO
        if not isinstance(nome, str) or Path(nome).name != nome or any(c in nome for c in '/\\:') or not nome.lower().endswith('.mp4'):
            raise ValueError(tr('galeria.nome_invalido'))
        raiz = Path(PASTA_DESTINO).resolve()
        origem = (raiz / nome).resolve()
        if origem.parent != raiz or not origem.is_file():
            raise ValueError(tr('galeria.nao_encontrado'))
        destino = webview.windows[0].create_file_dialog(webview.FileDialog.SAVE,
            save_filename=nome, file_types=('Video MP4 (*.mp4)',))
        if not destino:
            return {'cancelado': True}
        caminho = Path(destino if isinstance(destino, str) else destino[0])
        if caminho.resolve() != origem:
            shutil.copy2(origem, caminho)
        return {'cancelado': False, 'caminho': str(caminho)}

    def abrir_rede(self, plataforma, externo=False):
        if plataforma not in PORTAIS:
            raise ValueError(tr('social.plataforma'))
        nome, url = PORTAIS[plataforma]
        if externo:
            import webbrowser
            webbrowser.open(url)
            return True
        import webview
        with self._lock:
            window = self._windows.get(plataforma)
            if window and window in webview.windows:
                window.show()
                window.restore()
            else:
                # Sites terceiros não recebem a ponte Python do aplicativo.
                self._windows[plataforma] = webview.create_window(nome + ' — site oficial', url,
                    width=1100, height=800, min_size=(800, 600))
        return True
