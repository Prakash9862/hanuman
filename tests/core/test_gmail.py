from __future__ import annotations

import json
import time
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from hanuman.core import gmail


def test_credentials_prefers_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gmail, "CREDENTIALS_PATH", tmp_path / "missing.json")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "client-id")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "client-secret")

    assert gmail._credentials() == ("client-id", "client-secret")


def test_credentials_reads_installed_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    credentials_path = tmp_path / "credentials.json"
    credentials_path.write_text(
        json.dumps(
            {
                "installed": {
                    "client_id": "file-client",
                    "client_secret": "file-secret",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("GMAIL_CLIENT_ID", raising=False)
    monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)
    monkeypatch.setattr(gmail, "CREDENTIALS_PATH", credentials_path)

    assert gmail._credentials() == ("file-client", "file-secret")


def test_credentials_missing_raises_without_exposing_secret(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("GMAIL_CLIENT_ID", raising=False)
    monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)
    monkeypatch.setattr(gmail, "CREDENTIALS_PATH", tmp_path / "missing.json")

    with pytest.raises(RuntimeError, match="Identifiants Gmail absents"):
        gmail._credentials()


def test_load_token_rejects_missing_and_non_object_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    token_path = tmp_path / "token.json"
    monkeypatch.setattr(gmail, "TOKEN_PATH", token_path)

    with pytest.raises(RuntimeError, match="pas encore connecté"):
        gmail._load_token()

    token_path.write_text("[]", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Jeton Gmail illisible"):
        gmail._load_token()


def test_save_token_sets_expiry_and_restricts_permissions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    token_path = tmp_path / "secrets" / "token.json"
    monkeypatch.setattr(gmail, "TOKEN_PATH", token_path)
    monkeypatch.setattr(gmail.time, "time", lambda: 1_000.0)
    token = {"access_token": "dummy-access-token", "expires_in": 120}

    gmail._save_token(token)

    stored = json.loads(token_path.read_text(encoding="utf-8"))
    assert stored["expires_at"] == 1_060.0
    assert token_path.stat().st_mode & 0o777 == 0o600


def test_access_token_refreshes_expired_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved: list[dict[str, Any]] = []
    monkeypatch.delenv("GMAIL_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(
        gmail,
        "_load_token",
        lambda: {
            "access_token": "expired",
            "expires_at": time.time() - 1,
            "refresh_token": "dummy-refresh-token",
        },
    )
    monkeypatch.setattr(gmail, "_credentials", lambda: ("client", "secret"))
    monkeypatch.setattr(
        gmail,
        "_json_request",
        lambda *args, **kwargs: {"access_token": "fresh", "expires_in": 3600},
    )
    monkeypatch.setattr(gmail, "_save_token", lambda token: saved.append(dict(token)))

    assert gmail._access_token() == "fresh"
    assert saved == [
        {
            "access_token": "fresh",
            "expires_in": 3600,
            "refresh_token": "dummy-refresh-token",
        }
    ]


def test_access_token_rejects_expired_token_without_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GMAIL_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(
        gmail,
        "_load_token",
        lambda: {"access_token": "expired", "expires_at": 0},
    )

    with pytest.raises(RuntimeError, match="aucun refresh_token"):
        gmail._access_token()


def test_json_request_wraps_http_error_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = urllib.error.HTTPError(
        url="https://example.invalid",
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=None,
    )
    error.read = lambda: b'{"error":"invalid_token"}'  # type: ignore[method-assign]
    monkeypatch.setattr(
        gmail.urllib.request, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(error)
    )

    with pytest.raises(RuntimeError, match="Gmail API 401:"):
        gmail._json_request("https://example.invalid")


def test_body_decodes_nested_unicode_plain_text() -> None:
    encoded = "Qm9uam91ciDwn5mC".rstrip("=")
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/html", "body": {"data": "PGI+"}},
            {"mimeType": "text/plain", "body": {"data": encoded}},
        ],
    }

    assert gmail._body(payload) == "Bonjour 🙂"


def test_list_messages_ignores_malformed_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, Any] | None]] = []

    def fake_api(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        calls.append((path, params))
        if path == "messages":
            return {
                "messages": [None, {}, {"id": "m1"}],
                "nextPageToken": "next",
            }
        return {
            "id": "m1",
            "threadId": "t1",
            "labelIds": ["UNREAD", "IMPORTANT"],
            "snippet": "Aperçu",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Sujet"},
                    {"name": "From", "value": "Alice"},
                ]
            },
        }

    monkeypatch.setattr(gmail, "_api", fake_api)

    messages, next_page = gmail.list_messages(query="in:inbox", max_results=500, page_token="page")

    assert next_page == "next"
    assert len(messages) == 1
    assert messages[0].subject == "Sujet"
    assert messages[0].unread is True
    assert messages[0].important is True
    assert calls[0] == (
        "messages",
        {"q": "in:inbox", "maxResults": 100, "pageToken": "page"},
    )


def test_status_reports_configuration_and_connection_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gmail,
        "_credentials",
        lambda: (_ for _ in ()).throw(RuntimeError("configuration absente")),
    )
    unconfigured = gmail.status()
    assert unconfigured.configured is False
    assert unconfigured.connected is False

    monkeypatch.setattr(gmail, "_credentials", lambda: ("client", "secret"))
    monkeypatch.setattr(
        gmail,
        "_api",
        lambda path: (_ for _ in ()).throw(RuntimeError("jeton invalide")),
    )
    disconnected = gmail.status()
    assert disconnected.configured is True
    assert disconnected.connected is False
    assert disconnected.message == "jeton invalide"
