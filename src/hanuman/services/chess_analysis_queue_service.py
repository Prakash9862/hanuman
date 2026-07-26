from __future__ import annotations

import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hanuman.orchestrations.chess_analysis import (
    END_MARKER,
    START_MARKER,
    _chess_root,
    _game_paths,
    analyse_note,
)
from hanuman.services.atomic_write_service import atomic_write_text
from hanuman.services.chess_analysis_service import AnalysisConfig, StockfishAnalyzer
from hanuman.services.chess_path_safety_service import resolve_safe_destination
from hanuman.services.delimited_zone_service import (
    DelimitedZoneError,
    find_delimited_zone,
)

_STATE_FILENAME = ".hanuman-stockfish-state.json"
_LOCK = threading.Lock()
_STOP_EVENT = threading.Event()
_WORKER: threading.Thread | None = None


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _state_path() -> Path:
    return _chess_root() / _STATE_FILENAME


def _default_state() -> dict[str, Any]:
    return {
        "status": "idle",
        "total": 0,
        "completed": 0,
        "failed": 0,
        "remaining": 0,
        "current": None,
        "depth": None,
        "batch_limit": None,
        "started_at": None,
        "updated_at": _now(),
        "finished_at": None,
        "errors": [],
    }


def _write_state(state: dict[str, Any]) -> None:
    state["updated_at"] = _now()
    root = _chess_root()
    path = resolve_safe_destination(root, _state_path())
    atomic_write_text(path, json.dumps(state, ensure_ascii=False, indent=2))


def get_analysis_queue_status() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        return _default_state()

    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _default_state()

    if not isinstance(loaded, dict):
        return _default_state()

    state: dict[str, Any] = loaded

    if state.get("status") == "running" and (_WORKER is None or not _WORKER.is_alive()):
        state["status"] = "interrupted"
        state["current"] = None
        _write_state(state)

    return state


def _is_analysed(path: Path) -> bool:
    try:
        markdown = path.read_text(encoding="utf-8")
    except OSError:
        return False
    try:
        bounds = find_delimited_zone(
            markdown,
            START_MARKER,
            END_MARKER,
            label="d’analyse Chess",
        )
    except DelimitedZoneError:
        return False
    if bounds is None:
        return False
    block = markdown[bounds.start + len(START_MARKER) : bounds.end - len(END_MARKER)]
    return "Analyse non encore lancée." not in block and "### Ton bilan" in block


def count_analysis_queue() -> dict[str, int]:
    paths = _game_paths(_chess_root())
    analysed = sum(_is_analysed(path) for path in paths)
    return {"total": len(paths), "analysed": analysed, "pending": len(paths) - analysed}


def _run_queue(paths: list[Path], depth: int, batch_limit: int | None) -> None:
    global _WORKER
    state = _default_state()
    state.update(
        {
            "status": "running",
            "total": len(paths),
            "remaining": len(paths),
            "depth": depth,
            "batch_limit": batch_limit,
            "started_at": _now(),
            "errors": [],
        }
    )
    _write_state(state)

    config = AnalysisConfig(engine_path=os.environ.get("STOCKFISH_PATH"), depth=depth)
    try:
        with StockfishAnalyzer(config) as analyzer:
            for index, path in enumerate(paths, start=1):
                if _STOP_EVENT.is_set():
                    state["status"] = "stopped"
                    break
                state["current"] = str(path.relative_to(_chess_root()))
                state["remaining"] = len(paths) - index + 1
                _write_state(state)
                try:
                    analysis = analyse_note(path, analyzer, root=_chess_root())
                    if analysis is None:
                        raise ValueError("PGN absent ou illisible")
                    state["completed"] += 1
                except Exception as exc:  # noqa: BLE001 - chaque partie ne doit pas arrêter la file
                    state["failed"] += 1
                    state["errors"] = [
                        *state.get("errors", [])[-9:],
                        {"path": str(path), "error": str(exc)},
                    ]
                state["remaining"] = len(paths) - index
                _write_state(state)
        if state["status"] == "running":
            state["status"] = "done"
    except Exception as exc:  # noqa: BLE001 - état persistant pour diagnostic UI
        state["status"] = "failed"
        state["errors"] = [*state.get("errors", [])[-9:], {"path": "engine", "error": str(exc)}]
    finally:
        state["current"] = None
        state["finished_at"] = _now()
        _write_state(state)
        with _LOCK:
            _WORKER = None


def start_analysis_queue(depth: int = 12, limit: int | None = 25) -> dict[str, Any]:
    global _WORKER
    with _LOCK:
        if _WORKER is not None and _WORKER.is_alive():
            return {
                "ok": False,
                "message": "Une analyse Stockfish est déjà en cours",
                "state": get_analysis_queue_status(),
            }

        pending = [path for path in _game_paths(_chess_root()) if not _is_analysed(path)]
        if limit is not None:
            pending = pending[:limit]
        if not pending:
            state = _default_state()
            state.update({"status": "done", "finished_at": _now()})
            _write_state(state)
            return {"ok": True, "message": "Toutes les parties sont déjà analysées", "state": state}

        _STOP_EVENT.clear()
        _WORKER = threading.Thread(
            target=_run_queue,
            args=(pending, depth, limit),
            name="hanuman-stockfish-queue",
            daemon=True,
        )
        _WORKER.start()
    return {
        "ok": True,
        "message": f"Analyse lancée pour {len(pending)} partie(s)",
        "state": get_analysis_queue_status(),
    }


def stop_analysis_queue() -> dict[str, Any]:
    if _WORKER is None or not _WORKER.is_alive():
        return {
            "ok": False,
            "message": "Aucune analyse en cours",
            "state": get_analysis_queue_status(),
        }
    _STOP_EVENT.set()
    state = get_analysis_queue_status()
    state["status"] = "stopping"
    _write_state(state)
    return {"ok": True, "message": "Arrêt demandé après la position en cours", "state": state}
