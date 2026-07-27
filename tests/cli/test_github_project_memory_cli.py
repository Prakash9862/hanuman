from __future__ import annotations

import json
from io import StringIO

import pytest
from rich.console import Console

import hanuman.cli as cli
from hanuman.models.github_project_memory import FlowRun, GitHubProjectMemoryInput
from hanuman.orchestrations.github_project_memory import plan_github_project_memory
from tests.orchestrations.test_github_project_memory import (
    REPOSITORY,
    SHA_1,
    SHA_2,
    FakeGithubService,
    raw_commit,
)


def test_cli_delegates_to_flow_and_prints_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeGithubService([raw_commit(SHA_1)])
    calls: list[GitHubProjectMemoryInput] = []

    def fake_plan(flow_input: GitHubProjectMemoryInput) -> FlowRun:
        calls.append(flow_input)
        return plan_github_project_memory(flow_input, github_factory=lambda: service)

    monkeypatch.setattr(cli, "GITHUB_ALLOWED_REPOSITORIES", (REPOSITORY,))
    monkeypatch.setattr(cli, "plan_github_project_memory", fake_plan)
    output = StringIO()
    exit_code = cli.run_cli(
        [
            "flows",
            "github-project-memory",
            "plan",
            "--repository",
            REPOSITORY,
            "--branch",
            "main",
            "--max-commits",
            "10",
        ],
        console=Console(file=output, force_terminal=False, width=120),
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0].session_window_hours == 24
    assert calls[0].session_max_duration_hours == 12
    rendered = output.getvalue()
    assert "0 écriture exécutée" in rendered
    assert "not_applied" in rendered
    assert "Associations commit" not in rendered


def test_cli_json_output_contains_structured_run(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeGithubService([raw_commit(SHA_1)])

    def fake_plan(flow_input: GitHubProjectMemoryInput) -> FlowRun:
        return plan_github_project_memory(flow_input, github_factory=lambda: service)

    monkeypatch.setattr(cli, "GITHUB_ALLOWED_REPOSITORIES", (REPOSITORY,))
    monkeypatch.setattr(cli, "plan_github_project_memory", fake_plan)
    output = StringIO()
    exit_code = cli.run_cli(
        [
            "flows",
            "github-project-memory",
            "plan",
            "--repository",
            REPOSITORY,
            "--json",
        ],
        console=Console(file=output, force_terminal=False, width=200),
    )

    assert exit_code == 0
    payload = json.loads(output.getvalue())
    assert payload["result"]["status"] == "planned"
    assert payload["result"]["verification"] == "not_applied"
    assert payload["metrics"]["external_writes"] == 0
    assert payload["result"]["plan"]["schema_version"] == 2
    assert payload["input"]["session_max_duration_hours"] == 12


def test_detailed_plan_groups_commits_under_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeGithubService(
        [raw_commit(SHA_1, message="docs: Architecture des Flux"), raw_commit(SHA_2)]
    )

    def fake_plan(flow_input: GitHubProjectMemoryInput) -> FlowRun:
        return plan_github_project_memory(flow_input, github_factory=lambda: service)

    monkeypatch.setattr(cli, "GITHUB_ALLOWED_REPOSITORIES", (REPOSITORY,))
    monkeypatch.setattr(cli, "plan_github_project_memory", fake_plan)
    output = StringIO()
    exit_code = cli.run_cli(
        [
            "flows",
            "github-project-memory",
            "plan",
            "--repository",
            REPOSITORY,
            "--detailed-plan",
        ],
        console=Console(file=output, force_terminal=False, width=200),
    )

    rendered = output.getvalue()
    assert exit_code == 0
    assert "main — Documentation" in rendered
    assert "Development Sessions — détail" in rendered
    assert "Commits" in rendered
    assert "durée :" in rendered
    assert "ouverture :" in rendered
    assert SHA_1[:7] in rendered
    assert SHA_2[:7] in rendered
    assert rendered.index(SHA_1[:7]) < rendered.index(SHA_2[:7])
    assert "Associations commit → session" not in rendered
