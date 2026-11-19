"""Mensagens de erro legíveis para quem usa o app; o texto técnico vai para o relatório."""
import re

_BANNER = re.compile(r"^\s*(ffmpeg version|built with|configuration:|lib\w+\s+\d|Copyright)|--enable-|--disable-")

_CAUSAS = (
    (re.compile(r"HTTP error (404|410)|Server returned (404|410)|\b(404|410) Not Found|410 Gone"),
     "o link do vídeo expirou ou deixou de existir (o servidor respondeu {codigo}). Inicie de novo; "
     "se o link for de uma live, use o link do VOD."),
    (re.compile(r"HTTP error 403|Server returned 403|403 Forbidden"),
     "o servidor recusou o acesso ao vídeo (403). O VOD pode ser privado, exclusivo para inscritos, "
     "ou o link expirou. Inicie de novo."),
    (re.compile(r"Connection timed out|Connection refused|Connection reset|Failed to resolve|"
                r"Network is unreachable|getaddrinfo|I/O error", re.I),
     "a conexão com o servidor do vídeo falhou. Verifique a internet e inicie de novo."),
    (re.compile(r"No space left on device", re.I),
     "não há espaço livre em disco."),
)


def _texto(stderr):
    return stderr.decode(errors="replace") if isinstance(stderr, bytes) else (stderr or "")


def resumir_ffmpeg(stderr):
    """Uma frase sobre o que deu errado, sem o cabeçalho do FFmpeg nem URLs gigantes."""
    texto = _texto(stderr)
    for padrao, mensagem in _CAUSAS:
        achado = padrao.search(texto)
        if achado:
            codigo = next((g for g in achado.groups() if g), "") if achado.groups() else ""
            return mensagem.format(codigo=codigo or "erro")
    linhas = [l.strip() for l in texto.splitlines() if l.strip() and not _BANNER.search(l)]
    # URLs assinadas ocupam centenas de caracteres e não ajudam quem lê.
    linhas = [re.sub(r"https?://\S{60,}", "<link do vídeo>", l) for l in linhas]
    return " ".join(linhas[-3:])[:500] or "o FFmpeg terminou sem detalhar o erro."


class ErroFFmpeg(RuntimeError):
    """Falha do FFmpeg: mensagem curta na tela, saída técnica em ``detalhe``."""

    def __init__(self, contexto, stderr):
        self.detalhe = _texto(stderr)[-3000:]
        super().__init__(f"{contexto}: {resumir_ffmpeg(stderr)}")
