from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

from fastapi import FastAPI
from fastapi.routing import APIRoute
import importlib
from typing import Iterable
from hanuman.core.logging import configure_logging, get_logger
from hanuman.core.middleware import log_requests

configure_logging()
logger = get_logger(__name__)
logger.info("🚀 Lancement de Hanuman API (v5-dev)")

app = FastAPI(title="Hanuman API", version="1.1.0",
              description="API personnelle d’orchestration modulaire")
app.middleware("http")(log_requests)

def include_optional(app: FastAPI, modules: Iterable[str], attr: str = "router") -> None:
    for mod in modules:
        try:
            m = importlib.import_module(mod)
            r = getattr(m, attr)
            app.include_router(r)
            logger.info(f"✅ Router chargé: {mod}")
        except Exception as e:
            logger.warning(f"⏭️  Router ignoré ({mod}): {e}")

# Core routers (on n'inclut que ce qui existe réellement)
include_optional(app, [
    "hanuman.api.core.log",
    "hanuman.api.core.notion",
    "hanuman.api.core.github",
    "hanuman.api.core.chess_com",
    "hanuman.api.core.obsidian",
    "hanuman.api.core.openai",
    "hanuman.api.core.wikipedia",
    "hanuman.api.core.calendar",
])

from hanuman.api.core.status import router as status_router
app.include_router(status_router)
# v5 — orchestrations unifiées
include_optional(app, [
    "hanuman.api.core.log","hanuman.api.core.orchestrations_router"])

# Log des routes actives
active_routes = [r.path for r in app.routes if isinstance(r, APIRoute)]
logger.info(f"📦 Routes actives : {active_routes}")
