import pytest
from fastapi.testclient import TestClient

from hanuman.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_log_trace_endpoint(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    # Active les logs au niveau INFO
    caplog.set_level("INFO")

    response = client.get("/status")
    assert response.status_code == 200

    logs = [r.message for r in caplog.records]

    assert any("Requête reçue" in msg for msg in logs), "Log d'entrée manquant"
    assert any(
        "Exécution réussie" in msg or "Réponse sortante" in msg for msg in logs
    ), "Log de sortie manquant"

    # Si tu utilises @trace_endpoint + PingResult, on peut aussi tester :
    json_data = response.json()
    assert json_data.get("status") == "ok"
