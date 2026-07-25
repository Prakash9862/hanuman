from __future__ import annotations

import base64
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from email.header import decode_header, make_header
from pathlib import Path
from typing import Any

from hanuman.models.gmail import GmailMessageDetail, GmailMessageSummary, GmailStatus

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_ROOT = "https://gmail.googleapis.com/gmail/v1/users/me"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8000/gmail/auth/callback"
TOKEN_PATH = Path(os.environ.get("GMAIL_TOKEN_PATH", ".secrets/gmail-token.json"))
CREDENTIALS_PATH = Path(os.environ.get("GMAIL_CREDENTIALS_PATH", "config/gmail_credentials.json"))


def _json_request(
    url: str,
    *,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload = None
    request_headers = dict(headers or {})
    if data is not None:
        payload = urllib.parse.urlencode(data).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    request = urllib.request.Request(url, data=payload, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            loaded = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gmail API {exc.code}: {detail}") from exc
    if not isinstance(loaded, dict):
        raise RuntimeError("Réponse Gmail inattendue.")
    return loaded


def _credentials() -> tuple[str, str]:
    client_id = os.environ.get("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
    if client_id and client_secret:
        return client_id, client_secret
    if CREDENTIALS_PATH.is_file():
        payload = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
        config = payload.get("installed") or payload.get("web") or payload
        if isinstance(config, dict) and config.get("client_id") and config.get("client_secret"):
            return str(config["client_id"]), str(config["client_secret"])
    raise RuntimeError(
        "Identifiants Gmail absents. Ajoute config/gmail_credentials.json ou GMAIL_CLIENT_ID/GMAIL_CLIENT_SECRET."
    )


def _load_token() -> dict[str, Any]:
    if not TOKEN_PATH.is_file():
        raise RuntimeError("Gmail n’est pas encore connecté.")
    payload = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Jeton Gmail illisible.")
    return payload


def _save_token(token: dict[str, Any]) -> None:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    token["expires_at"] = time.time() + int(token.get("expires_in", 3600)) - 60
    TOKEN_PATH.write_text(json.dumps(token, indent=2), encoding="utf-8")
    TOKEN_PATH.chmod(0o600)


def authorization_url(state: str | None = None) -> tuple[str, str]:
    client_id, _ = _credentials()
    resolved_state = state or secrets.token_urlsafe(24)
    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": os.environ.get("GMAIL_REDIRECT_URI", DEFAULT_REDIRECT_URI),
            "response_type": "code",
            "scope": GMAIL_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": resolved_state,
        }
    )
    return f"{AUTH_URL}?{query}", resolved_state


def exchange_code(code: str) -> None:
    client_id, client_secret = _credentials()
    token = _json_request(
        TOKEN_URL,
        method="POST",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": os.environ.get("GMAIL_REDIRECT_URI", DEFAULT_REDIRECT_URI),
            "grant_type": "authorization_code",
        },
    )
    _save_token(token)


def _access_token() -> str:
    env_token = os.environ.get("GMAIL_ACCESS_TOKEN")
    if env_token:
        return env_token
    token = _load_token()
    access_token = token.get("access_token")
    if access_token and float(token.get("expires_at", 0)) > time.time():
        return str(access_token)
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("Le jeton Gmail a expiré et ne contient aucun refresh_token.")
    client_id, client_secret = _credentials()
    refreshed = _json_request(
        TOKEN_URL,
        method="POST",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    refreshed["refresh_token"] = refresh_token
    _save_token(refreshed)
    return str(refreshed["access_token"])


def _api(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{API_ROOT}/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return _json_request(url, headers={"Authorization": f"Bearer {_access_token()}"})


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except (LookupError, UnicodeDecodeError):
        return value


def _headers(payload: dict[str, Any]) -> dict[str, str]:
    headers = payload.get("headers") or []
    return {
        str(item.get("name", "")).lower(): _decode(str(item.get("value", "")))
        for item in headers
        if isinstance(item, dict)
    }


def _body(part: dict[str, Any]) -> str:
    mime_type = part.get("mimeType")
    data = (part.get("body") or {}).get("data")
    if mime_type == "text/plain" and data:
        return base64.urlsafe_b64decode(str(data) + "===").decode("utf-8", errors="replace")
    for child in part.get("parts") or []:
        if isinstance(child, dict):
            found = _body(child)
            if found:
                return found
    return ""


def _summary(message: dict[str, Any]) -> GmailMessageSummary:
    payload = message.get("payload") or {}
    headers = _headers(payload)
    labels = [str(label) for label in message.get("labelIds") or []]
    return GmailMessageSummary(
        id=str(message["id"]),
        thread_id=str(message.get("threadId", "")),
        subject=headers.get("subject") or "(Sans objet)",
        sender=headers.get("from") or "Inconnu",
        date=headers.get("date"),
        snippet=str(message.get("snippet", "")),
        unread="UNREAD" in labels,
        important="IMPORTANT" in labels,
        labels=labels,
    )


def status() -> GmailStatus:
    try:
        _credentials()
    except RuntimeError as exc:
        return GmailStatus(configured=False, connected=False, message=str(exc))
    try:
        profile = _api("profile")
        unread_result = _api("labels/INBOX")
        return GmailStatus(
            configured=True,
            connected=True,
            email=str(profile.get("emailAddress") or ""),
            unread=int(unread_result.get("messagesUnread") or 0),
        )
    except RuntimeError as exc:
        return GmailStatus(configured=True, connected=False, message=str(exc))


def list_messages(
    query: str = "in:inbox", max_results: int = 30, page_token: str | None = None
) -> tuple[list[GmailMessageSummary], str | None]:
    params: dict[str, Any] = {"q": query, "maxResults": max(1, min(max_results, 100))}
    if page_token:
        params["pageToken"] = page_token
    listed = _api("messages", params)
    messages: list[GmailMessageSummary] = []
    for ref in listed.get("messages") or []:
        if not isinstance(ref, dict) or not ref.get("id"):
            continue
        raw = _api(
            f"messages/{ref['id']}",
            {"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
        )
        messages.append(_summary(raw))
    return messages, listed.get("nextPageToken")


def get_message(message_id: str) -> GmailMessageDetail:
    raw = _api(f"messages/{urllib.parse.quote(message_id)}", {"format": "full"})
    summary = _summary(raw)
    headers = _headers(raw.get("payload") or {})
    return GmailMessageDetail(
        **summary.model_dump(),
        recipients=[item.strip() for item in headers.get("to", "").split(",") if item.strip()],
        cc=[item.strip() for item in headers.get("cc", "").split(",") if item.strip()],
        body=_body(raw.get("payload") or {}),
    )
