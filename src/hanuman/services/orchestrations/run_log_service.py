from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

# Chemins de base
THIS_FILE = Path(__file__).resolve()
HANUMAN_DIR = THIS_FILE.parents[2]  # .../src/hanuman
PROJECT_ROOT = HANUMAN_DIR.parents[1]  # .../
ORCHESTRATIONS_DIR = HANUMAN_DIR / "orchestrations"

LOG_PATH = PROJECT_ROOT / "data" / "orchestrations_runs.jsonl"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class RunLogEntry:
    orchestration: str
    started_at: str
    finished_at: str
    duration_seconds: float
    status: str  # "success" | "error"
    items_processed: Optional[int] = None
    error_message: Optional[str] = None


class RunContext:
    def __init__(self, orchestration: str) -> None:
        self.orchestration = orchestration
        self.started_at_dt = datetime.now(timezone.utc)
        self.finished_at_dt: Optional[datetime] = None
        self.status: str = "success"
        self.items_processed: Optional[int] = None
        self.error_message: Optional[str] = None

    def set_items_processed(self, count: int) -> None:
        self.items_processed = count

    def set_error(self, message: str) -> None:
        self.status = "error"
        self.error_message = message

    def to_entry(self) -> RunLogEntry:
        finished = self.finished_at_dt or datetime.now(timezone.utc)
        duration = (finished - self.started_at_dt).total_seconds()
        return RunLogEntry(
            orchestration=self.orchestration,
            started_at=self.started_at_dt.isoformat(),
            finished_at=finished.isoformat(),
            duration_seconds=duration,
            status=self.status,
            items_processed=self.items_processed,
            error_message=self.error_message,
        )


def _append_log(entry: RunLogEntry) -> None:
    """Ajoute une ligne JSONL au fichier de logs."""
    with LOG_PATH.open("a", encoding="utf-8") as f:
        json.dump(asdict(entry), f, ensure_ascii=False)
        f.write("\n")


@contextmanager
def log_run(orchestration: str) -> Generator[RunContext, None, None]:
    """
    À utiliser dans les orchestrations :

        with log_run("github_to_notion") as ctx:
            sync_github_issues_to_notion(...)
            ctx.set_items_processed(12)
    """
    ctx = RunContext(orchestration=orchestration)
    try:
        yield ctx
    except Exception as exc:  # noqa: BLE001
        ctx.set_error(str(exc))
        ctx.finished_at_dt = datetime.now(timezone.utc)
        _append_log(ctx.to_entry())
        raise
    else:
        ctx.finished_at_dt = datetime.now(timezone.utc)
        _append_log(ctx.to_entry())


def read_logs() -> List[RunLogEntry]:
    if not LOG_PATH.exists():
        return []
    entries: List[RunLogEntry] = []
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entries.append(RunLogEntry(**data))
            except Exception:
                # On ignore les lignes corrompues
                continue
    return entries


def list_orchestrations() -> List[str]:
    """
    Scanne src/hanuman/orchestrations pour lister automatiquement
    toutes les orchestrations (un fichier .py = une orchestration).
    """
    if not ORCHESTRATIONS_DIR.exists():
        return []

    names: List[str] = []
    for path in ORCHESTRATIONS_DIR.glob("*.py"):
        stem = path.stem
        if stem.startswith("_") or stem == "__init__":
            continue
        names.append(stem)

    return sorted(names)


def make_summary(limit_per_orchestration: int = 5) -> Dict[str, Any]:
    """
    Prépare les données pour le dashboard :

    {
      "orchestrations": [
        {
          "name": "github_to_notion",
          "runs": [ { ...RunLogEntry... }, ... ]
        },
        ...
      ]
    }
    """
    entries = read_logs()
    entries.sort(key=lambda e: e.started_at, reverse=True)

    # Regroupement par orchestration
    buckets: Dict[str, List[RunLogEntry]] = {}
    for entry in entries:
        bucket = buckets.setdefault(entry.orchestration, [])
        if len(bucket) >= limit_per_orchestration:
            continue
        bucket.append(entry)

    known = list_orchestrations()
    orchestrations: List[Dict[str, Any]] = []

    # D’abord les orchestrations détectées sur disque
    for name in known:
        run_entries = buckets.get(name, [])
        orchestrations.append(
            {
                "name": name,
                "runs": [asdict(e) for e in run_entries],
            }
        )

    # Puis celles qui ont des logs mais plus de fichier (au cas où)
    for name, run_entries in buckets.items():
        if name in known:
            continue
        orchestrations.append(
            {
                "name": name,
                "runs": [asdict(e) for e in run_entries],
            }
        )

    return {"orchestrations": orchestrations}
