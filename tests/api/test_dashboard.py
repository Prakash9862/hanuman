from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

from hanuman.api.routers import dashboard
from hanuman.main import app
from hanuman.services.orchestrations import run_log_service

client = TestClient(app)


def test_dashboard_summary_detects_orchestrations(tmp_path: Path, monkeypatch) -> None:
    # Prépare un faux dossier d’orchestrations
    orch_dir = tmp_path / "orchestrations"
    orch_dir.mkdir()
    (orch_dir / "foo_sync.py").write_text("# test\n", encoding="utf-8")
    (orch_dir / "__init__.py").write_text("# init\n", encoding="utf-8")

    log_path = tmp_path / "runs.jsonl"

    monkeypatch.setattr(run_log_service, "ORCHESTRATIONS_DIR", orch_dir)
    monkeypatch.setattr(run_log_service, "LOG_PATH", log_path)

    # Appel API
    resp = client.get("/dashboard/summary")
    assert resp.status_code == 200

    data = resp.json()
    orch_list = data["orchestrations"]
    names = [item["name"] for item in orch_list]
    assert "foo_sync" in names


def test_dashboard_page_returns_html() -> None:
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    text = resp.text
    assert "Hanuman Dashboard" in text
    assert "<html" in text.lower()


def test_run_orchestration_starts_process(monkeypatch) -> None:
    calls = []

    def fake_popen(cmd, cwd):
        calls.append((cmd, cwd))
        return None

    monkeypatch.setattr(
        "hanuman.api.routers.dashboard.list_orchestrations", lambda: ["foo"]
    )
    monkeypatch.setattr("hanuman.api.routers.dashboard.subprocess.Popen", fake_popen)

    resp = client.post("/dashboard/run/foo")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "started"
    assert payload["orchestration"] == "foo"

    assert calls, "Le processus devrait être lancé"
    cmd, cwd = calls[0]
    assert cmd[0] == sys.executable
    assert cmd[1:] == ["-m", "hanuman.orchestrations.foo"]
    assert Path(cwd).resolve() == dashboard.PROJECT_ROOT


def test_run_orchestration_unknown_name(monkeypatch) -> None:
    monkeypatch.setattr("hanuman.api.routers.dashboard.list_orchestrations", lambda: [])
