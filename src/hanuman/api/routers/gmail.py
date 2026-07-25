from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from hanuman.core.gmail import (
    authorization_url,
    exchange_code,
    get_message,
    list_messages,
    status,
)
from hanuman.models.gmail import GmailMessageDetail, GmailMessageList, GmailStatus

router = APIRouter(prefix="/gmail", tags=["gmail"])
_oauth_states: set[str] = set()


@router.get("/status", response_model=GmailStatus)
def gmail_status() -> GmailStatus:
    return status()


@router.get("/auth/start")
def gmail_auth_start() -> dict[str, str]:
    try:
        url, state = authorization_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _oauth_states.add(state)
    return {"url": url}


@router.get("/auth/callback", response_class=HTMLResponse)
def gmail_auth_callback(code: str, state: str) -> HTMLResponse:
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="État OAuth Gmail invalide ou expiré.")
    _oauth_states.discard(state)
    try:
        exchange_code(code)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return HTMLResponse(
        """
    <!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Gmail connecté</title>
    <style>body{font-family:system-ui;background:#111;color:#eee;display:grid;place-items:center;height:100vh;margin:0}main{text-align:center}h1{font-family:Georgia,serif;font-weight:400}p{color:#aaa}</style></head>
    <body><main><h1>Gmail est connecté à Hanuman.</h1><p>Tu peux fermer cette fenêtre et revenir dans Hanuman.</p></main></body></html>
    """
    )


@router.get("/messages", response_model=GmailMessageList)
def gmail_messages(
    query: str = Query(default="in:inbox"),
    max_results: int = Query(default=30, ge=1, le=100),
    page_token: str | None = None,
) -> GmailMessageList:
    try:
        messages, next_page_token = list_messages(query, max_results, page_token)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return GmailMessageList(messages=messages, total=len(messages), next_page_token=next_page_token)


@router.get("/important", response_model=GmailMessageList)
def gmail_important(max_results: int = Query(default=20, ge=1, le=100)) -> GmailMessageList:
    try:
        messages, next_page_token = list_messages(
            "in:inbox (is:important OR is:starred) newer_than:30d", max_results
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return GmailMessageList(messages=messages, total=len(messages), next_page_token=next_page_token)


@router.get("/messages/{message_id}", response_model=GmailMessageDetail)
def gmail_message(message_id: str) -> GmailMessageDetail:
    try:
        return get_message(message_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
