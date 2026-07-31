from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hanuman.api.routers.orchestrations import router as orchestrations_router
from hanuman.api.routers.settings import router as settings_router


def create_app() -> FastAPI:
    app = FastAPI(title="Hanuman API")

    # CORS (large par défaut, ajuste si besoin)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(orchestrations_router)
    app.include_router(settings_router)
    return app


app = create_app()
