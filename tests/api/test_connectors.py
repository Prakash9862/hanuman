from __future__ import annotations

from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_list_connectors() -> None:
    response = client.get("/connectors")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 8
    assert {item["id"] for item in payload["connectors"]} == {
        "gmail",
        "calendar",
        "github",
        "notion",
        "obsidian",
        "openai",
        "wikipedia",
        "chess-com",
    }


def test_get_connector() -> None:
    response = client.get("/connectors/calendar")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "calendar"
    assert "calendar.list_events" in payload["capabilities"]


def test_get_unknown_connector() -> None:
    response = client.get("/connectors/unknown")

    assert response.status_code == 404
    assert response.json()["detail"] == "Connecteur inconnu"


def test_list_capabilities() -> None:
    response = client.get("/connectors/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] > 0
    assert any(
        item["capability"] == "notes.write" and item["connector_ids"] == ["obsidian"]
        for item in payload["capabilities"]
    )


def test_find_capability_providers() -> None:
    response = client.get(
        "/connectors/providers",
        params={"capability": "ai.summarize"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["connectors"][0]["id"] == "openai"
