from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

from hanuman.services.orchestrations import run_log_service


def _read_lines(path: Path) -> List[dict]:
    lines: List[dict] = []
    if not path.exists():
        return lines
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        lines.append(json.loads(raw))
    return lines


def test_list_orchestrations_detects_py_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    orch_dir = tmp_path / "orchestrations"
    orch_dir.mkdir()

    # fichiers valides
    (orch_dir / "chess_to_obsidian.py").write_text("# test\n", encoding="utf-8")
    (orch_dir / "github_to_notion.py").write_text("# test\n", encoding="utf-8")
    # fichiers à ignorer
    (orch_dir / "__init__.py").write_text("# init\n", encoding="utf-8")
    (orch_dir / "_private.py").write_text("# private\n", encoding="utf-8")

    monkeypatch.setattr(run_log_service, "ORCHESTRATIONS_DIR", orch_dir)

    names = run_log_service.list_orchestrations()
    assert names == ["chess_to_obsidian", "github_to_notion"]


def test_log_run_success_writes_entry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log_path = tmp_path / "runs.jsonl"
    monkeypatch.setattr(run_log_service, "LOG_PATH", log_path)

    with run_log_service.log_run("github_to_notion") as ctx:
        ctx.set_items_processed(3)

    lines = _read_lines(log_path)
    assert len(lines) == 1
    entry = lines[0]
    assert entry["orchestration"] == "github_to_notion"
    assert entry["status"] == "success"
    assert entry["items_processed"] == 3
    assert "started_at" in entry and "finished_at" in entry
    assert entry["duration_seconds"] >= 0.0


def test_log_run_error_writes_error_entry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log_path = tmp_path / "runs_error.jsonl"
    monkeypatch.setattr(run_log_service, "LOG_PATH", log_path)

    with pytest.raises(RuntimeError):
        with run_log_service.log_run("obsidian_to_notion"):
            raise RuntimeError("boom")

    lines = _read_lines(log_path)
    assert len(lines) == 1
    entry = lines[0]
    assert entry["orchestration"] == "obsidian_to_notion"
    assert entry["status"] == "error"
    assert "boom" in (entry.get("error_message") or "")


def test_make_summary_groups_logs_by_orchestration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log_path = tmp_path / "runs_summary.jsonl"
    orch_dir = tmp_path / "orchestrations"
    orch_dir.mkdir()

    # Simule deux orchestrations présentes sur disque
    (orch_dir / "chess_to_obsidian.py").write_text("# test\n", encoding="utf-8")
    (orch_dir / "github_to_notion.py").write_text("# test\n", encoding="utf-8")

    monkeypatch.setattr(run_log_service, "LOG_PATH", log_path)
    monkeypatch.setattr(run_log_service, "ORCHESTRATIONS_DIR", orch_dir)

    # On écrit quelques logs via l’API officielle
    with run_log_service.log_run("chess_to_obsidian"):
        pass

    with run_log_service.log_run("github_to_notion") as ctx:
        ctx.set_items_processed(10)

    summary = run_log_service.make_summary(limit_per_orchestration=5)
    orchestrations = summary["orchestrations"]

    names = {item["name"] for item in orchestrations}
    assert "chess_to_obsidian" in names
    assert "github_to_notion" in names

    github_entry = next(item for item in orchestrations if item["name"] == "github_to_notion")
    runs = github_entry["runs"]
    assert len(runs) == 1
    assert runs[0]["items_processed"] == 10
