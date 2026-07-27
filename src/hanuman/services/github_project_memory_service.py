from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from hanuman.config.env import (
    GITHUB_ALLOWED_REPOSITORIES,
    GITHUB_PROJECT_MEMORY_BRANCH,
    GITHUB_PROJECT_MEMORY_REPOSITORY,
    NOTION_PROJECT_MEMORY_PARENT_PAGE_ID,
)
from hanuman.models.github_project_memory import FlowRun, GitHubProjectMemoryInput
from hanuman.orchestrations.github_project_memory_notion import (
    apply_github_project_memory,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUN_STORE = PROJECT_ROOT / "data" / "github_project_memory_runs.jsonl"
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "github-project-memory.yml"
FLOW_ID = "github-activity-notion-project-memory"
REQUIRED_SECRETS = ("NOTION_TOKEN", "NOTION_PROJECT_MEMORY_PARENT_PAGE_ID")
RunExecutor = Callable[[GitHubProjectMemoryInput], FlowRun]
_run_lock = threading.Lock()


class FlowAlreadyRunningError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubProjectMemoryConfig:
    repository: str = GITHUB_PROJECT_MEMORY_REPOSITORY
    branch: str = GITHUB_PROJECT_MEMORY_BRANCH
    max_commits: int = 100
    session_window_hours: int = 24
    session_max_duration_hours: int = 12
    allowed_repositories: tuple[str, ...] = ()

    def to_input(self) -> GitHubProjectMemoryInput:
        allowed = self.allowed_repositories or GITHUB_ALLOWED_REPOSITORIES or (self.repository,)
        return GitHubProjectMemoryInput(
            repository=self.repository,
            branch=self.branch,
            max_commits=self.max_commits,
            session_window_hours=self.session_window_hours,
            session_max_duration_hours=self.session_max_duration_hours,
            allowed_repositories=allowed,
        )


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Type non sérialisable : {type(value).__name__}")


def run_to_payload(run: FlowRun) -> dict[str, Any]:
    effects = run.result.effects

    def counts(prefix: str) -> dict[str, int]:
        return {
            "created": sum(effect.effect_type == f"{prefix}.create" for effect in effects),
            "updated": sum(effect.effect_type == f"{prefix}.update" for effect in effects),
            "unchanged": sum(effect.effect_type == f"{prefix}.no_change" for effect in effects),
        }

    payload = asdict(run)
    payload.update(
        {
            "duration_ms": float(run.metrics.get("duration_ms", 0)),
            "verification": run.result.verification,
            "repository": counts("repository"),
            "development_sessions": counts("development_session"),
            "commits": {
                "added": int(run.metrics.get("commits_added", 0)),
                "already_present": int(run.metrics.get("commits_already_present", 0)),
                "ignored": int(run.metrics.get("commits_ignored", 0)),
            },
            "failures": [asdict(error) for error in run.errors],
            "warnings": run.result.warnings,
            "fingerprint": run.result.plan.fingerprint if run.result.plan else None,
        }
    )
    return payload


def _run_store_path() -> Path:
    configured = os.environ.get("HANUMAN_PROJECT_MEMORY_RUN_STORE")
    return Path(configured).expanduser() if configured else DEFAULT_RUN_STORE


def save_run(run: FlowRun) -> None:
    path = _run_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        json.dump(run_to_payload(run), stream, default=_json_default, ensure_ascii=False)
        stream.write("\n")


def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    path = _run_store_path()
    if not path.exists():
        return []
    runs: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                runs.append(json.loads(line))
            except (json.JSONDecodeError, TypeError):
                continue
    return list(reversed(runs[-limit:]))


def get_run(run_id: str) -> dict[str, Any] | None:
    return next((run for run in list_runs(1000) if run.get("run_id") == run_id), None)


def execute_github_project_memory(
    *,
    trigger: str,
    config: GitHubProjectMemoryConfig | None = None,
    executor: RunExecutor = apply_github_project_memory,
) -> FlowRun:
    if not _run_lock.acquire(blocking=False):
        raise FlowAlreadyRunningError("Un Run GitHub Project Memory est déjà en cours.")
    try:
        run = executor((config or GitHubProjectMemoryConfig()).to_input())
        run.trigger = trigger
        save_run(run)
        return run
    finally:
        _run_lock.release()


def flow_configuration() -> dict[str, Any]:
    config = GitHubProjectMemoryConfig()
    visible_config = asdict(config)
    visible_config.pop("allowed_repositories")
    parent_id = (NOTION_PROJECT_MEMORY_PARENT_PAGE_ID or "").strip()
    configured_secrets = [
        name for name in REQUIRED_SECRETS if bool(os.environ.get(name, "").strip())
    ]
    return {
        "flow_id": FLOW_ID,
        "name": "GitHub Activity → Notion Project Memory",
        "description": "Projette l’activité GitHub en mémoire projet Notion vérifiée.",
        "backend_state": "available",
        "configuration": {
            **visible_config,
            "notion_destination": f"••••{parent_id[-6:]}" if parent_id else "Non configurée",
        },
        "automation": {
            "workflow_installed": WORKFLOW_PATH.is_file(),
            "trigger": "push sur main",
            "required_secrets": list(REQUIRED_SECRETS),
            "configured_locally": configured_secrets,
            "secrets_status": "unknown",
            "actions_url": (
                f"https://github.com/{config.repository}/actions/workflows/"
                "github-project-memory.yml"
            ),
        },
    }
