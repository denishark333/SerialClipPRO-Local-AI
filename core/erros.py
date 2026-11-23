"""Mensagens de erro legíveis para quem usa o app; o texto técnico vai para o relatório."""
import re
from core.textos import tr

_BANNER = re.compile(r"^\s*(ffmpeg version|built with|configuration:|lib\w+\s+\d|Copyright)|--enable-|--disable-")

_CAUSAS = (
    (re.compile(r"HTTP error (404|410)|Server returned (404|410)|\b(404|410) Not Found|410 Gone"),
     'ffmpeg.expirou'),
    (re.compile(r"HTTP error 403|Server returned 403|403 Forbidden"),
     'ffmpeg.recusou'),
    (re.compile(r"Connection timed out|Connection refused|Connection reset|Failed to resolve|"
                r"Network is unreachable|getaddrinfo|I/O error", re.I),
     'ffmpeg.conexao'),
    (re.compile(r"No space left on device", re.I),
     'ffmpeg.disco'),
)


def _texto(stderr):
    return stderr.decode(errors="replace") if isinstance(stderr, bytes) else (stderr or "")


def resumir_ffmpeg(stderr):
    """Uma frase sobre o que deu errado, sem o cabeçalho do FFmpeg nem URLs gigantes."""
    texto = _texto(stderr)
    for padrao, chave in _CAUSAS:
        achado = padrao.search(texto)
        if achado:
            codigo = next((g for g in achado.groups() if g), "") if achado.groups() else ""
            return tr(chave, codigo=codigo or "erro")
    linhas = [l.strip() for l in texto.splitlines() if l.strip() and not _BANNER.search(l)]
    # URLs assinadas ocupam centenas de caracteres e não ajudam quem lê.
    linhas = [re.sub(r"https?://\S{60,}", tr('ffmpeg.link_video'), l) for l in linhas]
    return " ".join(linhas[-3:])[:500] or tr('ffmpeg.sem_detalhe')


class ErroFFmpeg(RuntimeError):
    """Falha do FFmpeg: mensagem curta na tela, saída técnica em ``detalhe``."""

    def __init__(self, contexto, stderr):
        self.detalhe = _texto(stderr)[-3000:]
        super().__init__(f"{contexto}: {resumir_ffmpeg(stderr)}")
