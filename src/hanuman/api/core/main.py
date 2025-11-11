# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

APP_NAME = "Hanuman API"
APP_VERSION = "0.2.0"

log = logging.getLogger("hanuman.main")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def try_include(app: FastAPI, dotted: str, attr: str = "router", prefix: str | None = None):
    """Importe un module et inclut son router si présent. N'échoue jamais l'app."""
    try:
        mod = importlib.import_module(dotted)
        r = getattr(mod, attr, None)
        if r is None:
            log.warning("Router manquant dans %s (attr=%s)", dotted, attr)
            return False
        app.include_router(r, prefix=prefix or "")
        log.info("Routeur monté: %s", dotted)
        return True
    except Exception as e:
        log.warning("Routeur ignoré (%s): %s", dotted, e)
        return False


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=APP_VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root():
        return {"app": APP_NAME, "version": APP_VERSION, "status": "ok"}

    @app.get("/status")
    def status():
        keys = [
            "NOTION_TOKEN",
            "NOTION_VERSION",
            "NOTION_PARENT_ID",
            "OBSIDIAN_VAULT_DIR",
            "GITHUB_TOKEN",
            "OPENAI_API_KEY",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI",
        ]
        env = {k: (os.getenv(k) is not None) for k in keys}
        return {
            "env": env,
            "mounted": (
                sorted(list(app.router.routes_map.keys()))
                if hasattr(app.router, "routes_map")
                else "n/a"
            ),
        }

    # ====== Montage des routeurs connus (best-effort) ======
    # Orchestrations
    try_include(app, "hanuman.orchestrations.obsidian_to_notion")  # /obsidian/*
    try_include(
        app, "hanuman.orchestrations.github_sync_notion"
    )  # /github_sync_notion/* (si existant)
    try_include(app, "hanuman.orchestrations.calendar")  # /calendar/* (auth/ping/callback)

    # Core services ping (selon tes captures, tu avais ces routes)
    try_include(app, "hanuman.api.core.github")  # /github/ping
    try_include(app, "hanuman.api.core.wikipedia")  # /wikipedia/ping
    try_include(app, "hanuman.api.core.calendar")  # /calendar/ping
    try_include(app, "hanuman.api.core.openai")  # /openai/ping
    try_include(app, "hanuman.api.core.chess")  # /chess/ping
    try_include(app, "hanuman.api.core.notion")  # /notion/ping
    try_include(app, "hanuman.api.core.obsidian")  # /obsidian/ping

    return app


app = create_app()
