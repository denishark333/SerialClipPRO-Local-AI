"""Servidor local com cancelamento antes de aguardar tarefas em andamento."""
import asyncio
import os
import uvicorn

from core.execution import solicitar_cancelamento


class LocalServer(uvicorn.Server):
    def run(self, sockets=None):
        if os.name != 'nt':
            return super().run(sockets=sockets)
        # HTTP local usa sockets; FFmpeg é executado via subprocess síncrono.
        # Evita o transporte Proactor que falha na limpeza de conexões resetadas.
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            return runner.run(self.serve(sockets=sockets))

    def handle_exit(self, sig, frame):
        if not self.should_exit:
            print('Encerrando ClipPRO; cancelando pipeline e aguardando tarefas pendentes...', flush=True)
            solicitar_cancelamento()
        super().handle_exit(sig, frame)

    async def shutdown(self, sockets=None):
        solicitar_cancelamento()
        await super().shutdown(sockets=sockets)
