from __future__ import annotations

import pytest
from fastapi import HTTPException

from hanuman.api.routers import gmail
from hanuman.models.gmail import GmailStatus


@pytest.fixture(autouse=True)
def clear_oauth_states() -> None:
    gmail._oauth_states.clear()


def test_gmail_status_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = GmailStatus(configured=True, connected=False)
    monkeypatch.setattr(gmail, "status", lambda: expected)
    assert gmail.gmail_status() is expected


def test_auth_start_remembers_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gmail, "authorization_url", lambda: ("https://auth.test", "state"))

    assert gmail.gmail_auth_start() == {"url": "https://auth.test"}
    assert gmail._oauth_states == {"state"}


def test_auth_start_maps_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gmail,
        "authorization_url",
        lambda: (_ for _ in ()).throw(RuntimeError("credentials missing")),
    )

    with pytest.raises(HTTPException) as caught:
        gmail.gmail_auth_start()

    assert caught.value.status_code == 400


def test_auth_callback_rejects_unknown_or_reused_state() -> None:
    with pytest.raises(HTTPException, match="invalide"):
        gmail.gmail_auth_callback("code", "unknown")


def test_auth_callback_consumes_state_before_exchange(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gmail._oauth_states.add("state")
    monkeypatch.setattr(gmail, "exchange_code", lambda code: None)

    response = gmail.gmail_auth_callback("code", "state")

    assert response.status_code == 200
    assert "Gmail est connecté" in response.body.decode()
    assert "state" not in gmail._oauth_states


def test_auth_callback_maps_exchange_failure_and_consumes_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gmail._oauth_states.add("state")
    monkeypatch.setattr(
        gmail,
        "exchange_code",
        lambda code: (_ for _ in ()).throw(RuntimeError("token rejected")),
    )

    with pytest.raises(HTTPException) as caught:
        gmail.gmail_auth_callback("code", "state")

    assert caught.value.status_code == 502
    assert "state" not in gmail._oauth_states


def test_messages_builds_response_and_forwards_pagination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gmail, "list_messages", lambda *args: ([], "next"))

    result = gmail.gmail_messages("from:test", 5, "page")

    assert result.total == 0
    assert result.next_page_token == "next"


def test_important_and_message_detail_return_service_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gmail, "list_messages", lambda *args: ([], None))
    detail = object()
    monkeypatch.setattr(gmail, "get_message", lambda message_id: detail)

    assert gmail.gmail_important().total == 0
    assert gmail.gmail_message("message") is detail


@pytest.mark.parametrize("endpoint", ["messages", "important"])
def test_message_lists_map_runtime_errors(monkeypatch: pytest.MonkeyPatch, endpoint: str) -> None:
    monkeypatch.setattr(
        gmail,
        "list_messages",
        lambda *args: (_ for _ in ()).throw(RuntimeError("gmail unavailable")),
    )

    with pytest.raises(HTTPException) as caught:
        if endpoint == "messages":
            gmail.gmail_messages()
        else:
            gmail.gmail_important()

    assert caught.value.status_code == 502


def test_message_detail_maps_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gmail,
        "get_message",
        lambda message_id: (_ for _ in ()).throw(RuntimeError("not readable")),
    )

    with pytest.raises(HTTPException) as caught:
        gmail.gmail_message("message")

    assert caught.value.status_code == 502
