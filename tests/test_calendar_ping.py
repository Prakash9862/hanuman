from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_calendar_ping() -> None:
    response = client.get("/calendar/ping")
    assert response.status_code == 200

    data = response.json()
    assert "ok" in data
    assert "source" in data
    assert data["source"] == "calendar"

    if data["ok"]:
        assert "detail" in data
        assert "calendar_count" in data["detail"]
        assert isinstance(data["detail"]["calendar_count"], int)
    else:
        assert "error" in data
