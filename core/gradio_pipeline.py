"""Adaptador temporário para a interface Gradio; o processamento é compartilhado."""
import os

from core.config import PASTA_DESTINO, estado_pipeline
from core.pipeline import executar_pipeline_background
from core.execution import reservar_execucao


def pipeline_gradio(entrada, max_cortes, progress=None):
    max_cortes = int(max_cortes)
    execucao = reservar_execucao()
    if execucao is None:
        return [], "Já existe um pipeline em execução."
    executar_pipeline_background(entrada, max_cortes, execucao)
    videos = [os.path.join(PASTA_DESTINO, os.path.basename(url)) for url in estado_pipeline["videos"]]
    return videos, estado_pipeline["status"]
