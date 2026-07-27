from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from hanuman.services.github_project_memory_service import (
    FlowAlreadyRunningError,
    GitHubProjectMemoryConfig,
    execute_github_project_memory,
    flow_configuration,
    get_run,
    list_runs,
    run_to_payload,
)

router = APIRouter(prefix="/flows/github-project-memory", tags=["flows"])


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository: str | None = Field(default=None, pattern=r"^[^/\s]+/[^/\s]+$")
    branch: str | None = Field(default=None, min_length=1, max_length=255)
    max_commits: int | None = Field(default=None, ge=1, le=100)
    session_window_hours: int | None = Field(default=None, ge=1, le=720)
    session_max_duration_hours: int | None = Field(default=None, ge=1, le=168)


@router.get("")
def github_project_memory_configuration() -> dict[str, Any]:
    return flow_configuration()


@router.post("/runs")
def create_github_project_memory_run(body: RunRequest | None = None) -> JSONResponse:
    overrides = body.model_dump(exclude_none=True) if body else {}
    config = GitHubProjectMemoryConfig(**overrides)
    try:
        run = execute_github_project_memory(trigger="manual_ui", config=config)
    except FlowAlreadyRunningError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    payload = run_to_payload(run)
    return JSONResponse(
        status_code=200 if run.status in {"succeeded", "skipped"} else 502,
        content=jsonable_encoder(payload),
    )


@router.get("/runs")
def github_project_memory_runs(
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    runs = list_runs(limit)
    return {"runs": runs, "total": len(runs)}


@router.get("/runs/{run_id}")
def github_project_memory_run(run_id: str) -> dict[str, Any]:
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run introuvable.")
    return run
