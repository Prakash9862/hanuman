from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from hanuman.core.token_manager import save_token_json
from hanuman.main import app


def test_status_token_previews_debug_mode(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:

    client = TestClient(app)
    # Active DEBUG mode
    monkeypatch.setenv("DEBUG", "true")

    # Redirige le dossier secrets vers un dossier temporaire isolé
    monkeypatch.setattr("hanuman.core.token_manager.TOKEN_DIR", tmp_path)

    # Crée un faux token google_calendar
    save_token_json("google_calendar", {"token": "ya29.abcdef123456"})

    response = client.get("/status")
    assert response.status_code == 200
    json = response.json()

    assert "token_previews" in json
    assert "google_calendar" in json["token_previews"]
    assert json["token_previews"]["google_calendar"] == "ya29.a..."
