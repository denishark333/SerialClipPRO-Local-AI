"""Controle de uma execução local, compartilhado por todas as interfaces."""
import os
import subprocess
import threading
import time
from core.textos import tr

from core.config import estado_pipeline, estado_lock, formatar_tempo


class PipelineCancelado(Exception):
    pass


class Execucao:
    def __init__(self):
        self.cancelamento = threading.Event()

    def verificar(self):
        if self.cancelamento.is_set():
            raise PipelineCancelado("Pipeline cancelado pelo usuário.")

    def progresso_download(self, _):
        self.verificar()


_ativa = None
_manutencao = False


def operacao_em_andamento():
    with estado_lock:
        return _ativa is not None or _manutencao


def reservar_manutencao():
    global _manutencao
    with estado_lock:
        if _ativa is not None or _manutencao:
            return False
        _manutencao = True
        return True


def liberar_manutencao():
    global _manutencao
    with estado_lock:
        _manutencao = False


def reservar_execucao():
    global _ativa
    with estado_lock:
        if _ativa is not None or _manutencao:
            return None
        _ativa = Execucao()
        estado_pipeline.update(
            status=tr('status.preparando_execucao'), etapa=0, progresso_pct=0,
            videos=[], tempo_inicio=time.time(), tempo_decorrido="00:00",
            tempo_total="00:00", executando=True, cancelando=False, cancelado=False,
            relatorio_curadoria=None, resumo_curadoria=None,
            tempos_etapas={}, encoder=None, encoder_tentativa=None,
        )
        return _ativa


def solicitar_cancelamento():
    with estado_lock:
        if _ativa is None:
            return False
        _ativa.cancelamento.set()
        estado_pipeline.update(cancelando=True, status=tr('status.cancelando'))
        return True


def finalizar_execucao(execucao):
    global _ativa
    with estado_lock:
        if _ativa is execucao:
            if execucao.cancelamento.is_set():
                estado_pipeline.update(status=tr('status.cancelado'), etapa=-1, cancelado=True)
            estado_pipeline.update(executando=False, cancelando=False, encoder_tentativa=None)
            estado_pipeline["tempo_total"] = formatar_tempo(time.time() - estado_pipeline["tempo_inicio"])
            estado_pipeline["tempo_decorrido"] = estado_pipeline["tempo_total"]
            _ativa = None


def executar_comando(comando, execucao=None, timeout=None, check=False, monitor=None, intervalo_monitor=15, **kwargs):
    """Drena pipes enquanto aguarda e encerra somente o subprocesso desta operação."""
    if execucao:
        execucao.verificar()
    if os.name == "nt":
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW)
    if kwargs.get("text"):
        kwargs.setdefault("errors", "replace")
    inicio = time.monotonic()
    proximo_monitor = inicio + intervalo_monitor
    with subprocess.Popen(comando, **kwargs) as processo:
        try:
            while True:
                if execucao:
                    execucao.verificar()
                if timeout is not None and time.monotonic() - inicio >= timeout:
                    raise subprocess.TimeoutExpired(comando, timeout)
                try:
                    stdout, stderr = processo.communicate(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    agora = time.monotonic()
                    if monitor and agora >= proximo_monitor:
                        monitor(agora - inicio)
                        proximo_monitor = agora + intervalo_monitor
                    continue
        except BaseException:
            processo.kill()
            processo.communicate()
            raise
        if execucao:
            execucao.verificar()
        resultado = subprocess.CompletedProcess(comando, processo.returncode, stdout, stderr)
        if check:
            resultado.check_returncode()
        return resultado
