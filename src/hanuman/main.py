# src/hanuman/api/core/main.py
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from hanuman.api.core.brain import router as brain_router
from hanuman.api.core.calendar import router as calendar_router
from hanuman.api.core.chess_com import router as chess_router
from hanuman.api.core.github import router as github_router
from hanuman.api.core.log import router as log_router
from hanuman.api.core.notion import router as notion_router
from hanuman.api.core.obsidian import router as obsidian_router
from hanuman.api.core.openai import router as openai_router
from hanuman.api.core.status import router as status_router
from hanuman.api.core.wikipedia import router as wikipedia_router
from hanuman.api.routers import chess_to_obsidian as chess_to_obsidian_router
from hanuman.api.routers import dashboard
from hanuman.api.routers.orchestrations import router as orchestrations_router
from hanuman.core.logging import configure_logging, get_logger
from hanuman.core.middleware import log_requests

# ---- config runtime
load_dotenv(dotenv_path=".env", override=True)
configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Hanuman API", version="0.1.0")

# CORS (optionnel, large)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# middleware custom
app.middleware("http")(log_requests)

# routers
for r in (
    status_router,
    obsidian_router,
    notion_router,
    openai_router,
    brain_router,
    github_router,
    wikipedia_router,
    calendar_router,
    chess_router,
    log_router,
    orchestrations_router,
    chess_to_obsidian_router.router,
    dashboard.router,
):
    app.include_router(r)


def list_routes() -> list[str]:
    return [
        f"{route.name}: {route.path}"
        for route in app.routes
        if isinstance(route, APIRoute)
    ]
