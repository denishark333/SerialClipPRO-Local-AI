import os
import socket
import webbrowser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from api.media import MediaFiles

from core.config import BASE_DIR, PASTA_DESTINO, PASTA_EXPORTADOS, PASTA_TEMP
from api.routes import router
from api.branding import router as branding_router
from api.environment import router as environment_router
from api.social import router as social_router
from api.review import router as review_router
from core.version import APP_VERSION

app = FastAPI(title="Serial ClipPRO - Stream/Zero-Download Engine", version=APP_VERSION)

allowed_origins = [
    origem.strip()
    for origem in os.getenv("CLIPPRO_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origem.strip()
]

# Só aceita requisições endereçadas ao próprio computador. Sem isso, um site
# aberto no navegador poderia usar DNS rebinding para apontar um domínio dele
# para 127.0.0.1 e chamar esta API (listar, apagar ou gerar cortes).
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/videos", MediaFiles(directory=PASTA_DESTINO), name="videos")
app.mount("/temp_clip_cache", StaticFiles(directory=PASTA_TEMP), name="temp_clip_cache")
app.mount("/exportados", StaticFiles(directory=PASTA_EXPORTADOS), name="exportados")

app.include_router(router, prefix="/api")
app.include_router(branding_router, prefix="/api")
app.include_router(environment_router, prefix="/api")
app.include_router(social_router, prefix="/api")
app.include_router(review_router, prefix="/api")

# API and media routes take precedence over the built React interface.
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

def run():
    import uvicorn
    from core.local_server import LocalServer

    class BrowserServer(LocalServer):
        async def startup(self, sockets=None):
            await super().startup(sockets=sockets)
            if self.started:
                webbrowser.open("http://127.0.0.1:8765", new=2)

    # Reserva a porta antes de iniciar ou abrir o navegador.
    with socket.socket() as sock:
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            sock.bind(('127.0.0.1', 8765))
        except OSError as erro:
            raise SystemExit(
                'Não foi possível abrir a porta 8765. Se o ClipPRO já estiver '
                'rodando, use a aba existente ou encerre o terminal anterior '
                'com Ctrl+C antes de reabrir. Detalhes: ' + str(erro)
            ) from erro
        server = BrowserServer(uvicorn.Config(app, host='127.0.0.1', port=8765, log_level='warning'))
        print('Serial ClipPRO: http://127.0.0.1:8765 — encerre com Ctrl+C.', flush=True)
        server.run(sockets=[sock])

if __name__ == "__main__":
    run()
