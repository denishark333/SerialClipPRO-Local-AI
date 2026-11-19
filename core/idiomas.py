"""Idioma falado na live, usado pelo Whisper e informado à curadoria."""

#: Código do Whisper -> nome em português (para a curadoria e a interface).
IDIOMAS = {
    "pt": "português",
    "en": "inglês",
    "es": "espanhol",
    "fr": "francês",
    "de": "alemão",
    "it": "italiano",
    "ja": "japonês",
    "ko": "coreano",
    "auto": "detectado automaticamente",
}
PADRAO = "pt"


def para_whisper(codigo):
    """Código para o Whisper; None deixa o modelo detectar o idioma de cada trecho."""
    return None if codigo == "auto" else codigo


def nome(codigo):
    return IDIOMAS.get(codigo, codigo)
