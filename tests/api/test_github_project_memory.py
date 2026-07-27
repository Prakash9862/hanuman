from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import hanuman.api.routers.github_project_memory as router_module
import hanuman.services.github_project_memory_service as flow_service
from hanuman.models.github_project_memory import (
    FlowRun,
    GitHubProjectMemoryInput,
    PlannedEffect,
    StructuredError,
)
from hanuman.orchestrations.github_project_memory import plan_github_project_memory
from tests.orchestrations.test_github_project_memory import (
    REPOSITORY,
    SHA_1,
    FakeGithubService,
    raw_commit,
)


def successful_run() -> FlowRun:
    github = FakeGithubService([raw_commit(SHA_1)])
    flow_input = GitHubProjectMemoryInput(
        repository=REPOSITORY,
        branch="main",
        allowed_repositories=(REPOSITORY,),
    )
    run = plan_github_project_memory(flow_input, github_factory=lambda: github)
    run.result.status = "verified"
    run.result.verification = "passed"
    run.result.summary = "Synchronisation vérifiée."
    run.result.effects = [
        PlannedEffect("repository.no_change", "repo", "inchangé"),
        PlannedEffect("development_session.update", "session", "mise à jour"),
    ]
    run.metrics.update(
        {
            "commits_added": 1,
            "commits_already_present": 2,
            "commits_ignored": 0,
        }
    )
    return run


def test_api_run_delegates_and_returns_business_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, flow_service.GitHubProjectMemoryConfig]] = []

    def execute(*, trigger: str, config: flow_service.GitHubProjectMemoryConfig) -> FlowRun:
        calls.append((trigger, config))
        return successful_run()

    monkeypatch.setattr(router_module, "execute_github_project_memory", execute)
    response = router_module.create_github_project_memory_run(
        router_module.RunRequest(max_commits=100, session_window_hours=24)
    )

    assert response.status_code == 200
    assert calls[0][0] == "manual_ui"
    assert calls[0][1].max_commits == 100
    body = json.loads(response.body)
    assert body["verification"] == "passed"
    assert body["repository"] == {"created": 0, "updated": 0, "unchanged": 1}
    assert body["development_sessions"]["updated"] == 1
    assert body["commits"] == {"added": 1, "already_present": 2, "ignored": 0}
    assert body["fingerprint"]
    assert body["idempotency_key"]


@pytest.mark.parametrize(
    "payload",
    [
        {"repository": "invalid"},
        {"max_commits": 0},
        {"max_commits": 101},
        {"session_window_hours": 0},
    ],
)
def test_api_validates_parameters(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        router_module.RunRequest(**payload)


def test_failed_run_is_not_hidden_behind_http_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = successful_run()
    error = StructuredError("notion_verification", "verification", "Valeur différente.")
    run.status = "failed"
    run.result.status = "failed"
    run.result.verification = "failed"
    run.result.summary = "Vérification échouée."
    run.errors = [error]
    monkeypatch.setattr(
        router_module,
        "execute_github_project_memory",
        lambda **kwargs: run,
    )

    response = router_module.create_github_project_memory_run(router_module.RunRequest())

    assert response.status_code == 502
    assert json.loads(response.body)["failures"][0]["code"] == "notion_verification"


def test_concurrent_run_returns_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        router_module,
        "execute_github_project_memory",
        lambda **kwargs: (_ for _ in ()).throw(
            flow_service.FlowAlreadyRunningError("déjà en cours")
        ),
    )
    with pytest.raises(HTTPException) as caught:
        router_module.create_github_project_memory_run(router_module.RunRequest())
    assert caught.value.status_code == 409
    assert "déjà en cours" in caught.value.detail


def test_configuration_exposes_no_secret_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "notion-secret-value")
    response = router_module.github_project_memory_configuration()
    serialized = json.dumps(response)
    assert "notion-secret-value" not in serialized
    assert response["automation"]["secrets_status"] == "unknown"


def test_run_history_is_persisted_and_readable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = tmp_path / "runs.jsonl"
    monkeypatch.setenv("HANUMAN_PROJECT_MEMORY_RUN_STORE", str(store))
    run = successful_run()

    flow_service.save_run(run)

    assert flow_service.list_runs()[0]["run_id"] == run.run_id
    assert flow_service.get_run(run.run_id)["verification"] == "passed"  # type: ignore[index]


def test_application_service_calls_existing_orchestration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HANUMAN_PROJECT_MEMORY_RUN_STORE", str(tmp_path / "runs.jsonl"))
    calls: list[GitHubProjectMemoryInput] = []

    def executor(flow_input: GitHubProjectMemoryInput) -> FlowRun:
        calls.append(flow_input)
        return successful_run()

    run = flow_service.execute_github_project_memory(
        trigger="github_actions",
        config=flow_service.GitHubProjectMemoryConfig(
            repository=REPOSITORY,
            allowed_repositories=(REPOSITORY,),
        ),
        executor=executor,
    )

    assert len(calls) == 1
    assert run.trigger == "github_actions"
