"""Ordem estável compartilhada pela galeria e pela revisão."""
import re


def chave_corte(nome):
    match = re.fullmatch(r'corte_(\d{8})_(\d{6})(?:_([0-9a-f]+))?_(\d+)\.mp4', nome, re.IGNORECASE)
    if match:
        dia, hora, sessao, numero = match.groups()
        return (0, -int(dia + hora), sessao or '', int(numero), nome)
    return (1, 0, '', 0, nome.casefold())
