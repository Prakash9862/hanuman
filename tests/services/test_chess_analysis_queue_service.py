from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from hanuman.services import chess_analysis_queue_service as queue


@pytest.fixture(autouse=True)
def reset_worker_state():
    queue._WORKER = None
    queue._STOP_EVENT.clear()
    yield
    queue._WORKER = None
    queue._STOP_EVENT.clear()


def test_state_round_trip_and_invalid_files(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(queue, "_validated_chess_root", lambda: tmp_path)
    monkeypatch.setattr(queue, "resolve_safe_destination", lambda root, path: path)
    monkeypatch.setattr(
        queue,
        "atomic_write_text",
        lambda path, text: path.write_text(text, encoding="utf-8"),
    )
    assert queue.get_analysis_queue_status()["status"] == "idle"

    state = queue._default_state()
    queue._write_state(state)
    assert queue.get_analysis_queue_status()["status"] == "idle"

    queue._state_path(tmp_path).write_text("{bad", encoding="utf-8")
    assert queue.get_analysis_queue_status()["status"] == "idle"
    queue._state_path(tmp_path).write_text("[]", encoding="utf-8")
    assert queue.get_analysis_queue_status()["status"] == "idle"


def test_status_marks_orphaned_running_worker_interrupted(tmp_path: Path, monkeypatch):
    path = queue._state_path(tmp_path)
    path.write_text(json.dumps({"status": "running", "current": "game.md"}), encoding="utf-8")
    written = []
    monkeypatch.setattr(queue, "_validated_chess_root", lambda: tmp_path)
    monkeypatch.setattr(queue, "resolve_safe_destination", lambda root, target: target)
    monkeypatch.setattr(queue, "_write_state", lambda state, root=None: written.append(dict(state)))

    state = queue.get_analysis_queue_status()

    assert state["status"] == "interrupted"
    assert state["current"] is None
    assert written


def test_is_analysed_distinguishes_complete_placeholder_and_invalid(tmp_path: Path):
    complete = tmp_path / "complete.md"
    complete.write_text(
        f"{queue.START_MARKER}\n### Ton bilan\nOK\n{queue.END_MARKER}",
        encoding="utf-8",
    )
    placeholder = tmp_path / "placeholder.md"
    placeholder.write_text(
        f"{queue.START_MARKER}\nAnalyse non encore lancée.\n{queue.END_MARKER}",
        encoding="utf-8",
    )
    malformed = tmp_path / "malformed.md"
    malformed.write_text(f"{queue.END_MARKER}\n{queue.START_MARKER}", encoding="utf-8")

    assert queue._is_analysed(complete) is True
    assert queue._is_analysed(placeholder) is False
    assert queue._is_analysed(malformed) is False
    assert queue._is_analysed(tmp_path / "missing.md") is False


def test_count_queue_uses_game_paths(tmp_path: Path, monkeypatch):
    paths = [tmp_path / "one.md", tmp_path / "two.md"]
    monkeypatch.setattr(queue, "_validated_chess_root", lambda: tmp_path)
    monkeypatch.setattr(queue, "_game_paths", lambda root: paths)
    monkeypatch.setattr(queue, "_is_analysed", lambda path: path.name == "one.md")
    assert queue.count_analysis_queue() == {"total": 2, "analysed": 1, "pending": 1}


def test_run_queue_records_success_and_per_game_failure(tmp_path: Path, monkeypatch):
    paths = [tmp_path / "one.md", tmp_path / "two.md"]
    states = []

    class Analyzer:
        def __init__(self, config):
            self.config = config

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    monkeypatch.setattr(queue, "StockfishAnalyzer", Analyzer)
    monkeypatch.setattr(queue, "chess_player_name", lambda: "Player")
    monkeypatch.setattr(queue, "_write_state", lambda state, root=None: states.append(dict(state)))
    monkeypatch.setattr(
        queue,
        "analyse_note",
        lambda path, analyzer, root: object() if path.name == "one.md" else None,
    )

    queue._run_queue(paths, tmp_path, 14, 2)

    final = states[-1]
    assert final["status"] == "done"
    assert final["completed"] == 1
    assert final["failed"] == 1
    assert final["errors"][0]["path"].endswith("two.md")
    assert queue._WORKER is None


def test_run_queue_records_engine_failure_and_stop(tmp_path: Path, monkeypatch):
    states = []

    class BrokenAnalyzer:
        def __init__(self, config):
            pass

        def __enter__(self):
            raise RuntimeError("engine missing")

        def __exit__(self, *args):
            return None

    monkeypatch.setattr(queue, "StockfishAnalyzer", BrokenAnalyzer)
    monkeypatch.setattr(queue, "_write_state", lambda state, root=None: states.append(dict(state)))
    queue._run_queue([tmp_path / "one.md"], tmp_path, 12, None)
    assert states[-1]["status"] == "failed"
    assert states[-1]["errors"][-1] == {"path": "engine", "error": "engine missing"}

    queue._STOP_EVENT.set()

    class Analyzer(BrokenAnalyzer):
        def __enter__(self):
            return self

    monkeypatch.setattr(queue, "StockfishAnalyzer", Analyzer)
    queue._run_queue([tmp_path / "one.md"], tmp_path, 12, None)
    assert states[-1]["status"] == "stopped"


def test_start_queue_handles_running_empty_and_pending(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(queue, "_validated_chess_root", lambda: tmp_path)
    monkeypatch.setattr(queue, "_write_state", lambda state, root=None: None)
    monkeypatch.setattr(queue, "get_analysis_queue_status", lambda: {"status": "running"})
    queue._WORKER = SimpleNamespace(is_alive=lambda: True)
    assert queue.start_analysis_queue()["ok"] is False

    queue._WORKER = None
    monkeypatch.setattr(queue, "_game_paths", lambda root: [])
    assert "déjà analysées" in queue.start_analysis_queue()["message"]

    started = []

    class FakeThread:
        def __init__(self, **kwargs):
            started.append(kwargs)

        def start(self):
            started.append("started")

        def is_alive(self):
            return True

    paths = [tmp_path / "one.md", tmp_path / "two.md"]
    monkeypatch.setattr(queue, "_game_paths", lambda root: paths)
    monkeypatch.setattr(queue, "_is_analysed", lambda path: False)
    monkeypatch.setattr(queue.threading, "Thread", FakeThread)

    result = queue.start_analysis_queue(depth=16, limit=1)

    assert result["ok"] is True
    assert "1 partie" in result["message"]
    assert started[0]["args"] == ([paths[0]], tmp_path, 16, 1)


def test_stop_queue_handles_idle_and_running(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(queue, "get_analysis_queue_status", lambda: {"status": "running"})
    assert queue.stop_analysis_queue()["ok"] is False

    queue._WORKER = SimpleNamespace(is_alive=lambda: True)
    written = []
    monkeypatch.setattr(queue, "_validated_chess_root", lambda: tmp_path)
    monkeypatch.setattr(queue, "_write_state", lambda state, root=None: written.append(dict(state)))

    result = queue.stop_analysis_queue()

    assert result["ok"] is True
    assert queue._STOP_EVENT.is_set()
    assert written[-1]["status"] == "stopping"
