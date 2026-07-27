from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from hanuman.models.github_project_memory import (
    GitHubProjectMemoryInput,
    NormalizedCommit,
)
from hanuman.orchestrations.github_project_memory import (
    group_development_sessions,
    plan_github_project_memory,
)
from hanuman.services.core.github_service import (
    GithubApiError,
    GithubAuthError,
    GithubCommit,
    GithubRepo,
    GithubService,
)

REPOSITORY = "example/project"
REPOSITORY_ID = 4242
SHA_1 = "1" * 40
SHA_2 = "2" * 40
SHA_3 = "3" * 40


def raw_commit(
    sha: str,
    *,
    parent: str | None = None,
    committed_at: datetime | None = None,
    message: str = "Implement deterministic planning\n\nHidden body",
) -> GithubCommit:
    timestamp = (committed_at or datetime(2026, 7, 1, 9, tzinfo=UTC)).isoformat()
    return GithubCommit(
        sha=sha,
        parent_shas=(parent,) if parent else (),
        authored_at=timestamp,
        committed_at=timestamp,
        git_author="Example Developer",
        github_author="example-user",
        message=message,
        html_url=f"https://github.example/{REPOSITORY}/commit/{sha}",
    )


class FakeGithubService(GithubService):
    def __init__(
        self,
        commits: list[GithubCommit],
        *,
        error: Exception | None = None,
    ) -> None:
        self.commits = commits
        self.error = error
        self.requests: list[dict[str, Any]] = []

    def get_repo(self, full_name: str | None = None) -> GithubRepo:
        if self.error:
            raise self.error
        return GithubRepo(
            repository_id=REPOSITORY_ID,
            owner="example",
            name="project",
            full_name=REPOSITORY,
            description="Fixture anonymisée",
            stars=0,
            forks=0,
            html_url=f"https://github.example/{REPOSITORY}",
            default_branch="main",
        )

    def list_commits(
        self,
        full_name: str,
        *,
        ref: str,
        start_sha: str | None = None,
        max_commits: int = 50,
    ) -> list[GithubCommit]:
        self.requests.append(
            {
                "full_name": full_name,
                "ref": ref,
                "start_sha": start_sha,
                "max_commits": max_commits,
            }
        )
        return self.commits[:max_commits]


def flow_input(**overrides: Any) -> GitHubProjectMemoryInput:
    values: dict[str, Any] = {
        "repository": REPOSITORY,
        "branch": "main",
        "max_commits": 50,
        "session_window_hours": 24,
        "allowed_repositories": (REPOSITORY,),
    }
    values.update(overrides)
    return GitHubProjectMemoryInput(**values)


def normalized_commit(
    repository_id: int,
    sha: str,
    *,
    branch: str = "refs/heads/main",
    parent: str | None = None,
    committed_at: datetime | None = None,
    subject: str = "Change",
) -> NormalizedCommit:
    timestamp = committed_at or datetime(2026, 7, 1, 9, tzinfo=UTC)
    return NormalizedCommit(
        repository_id=repository_id,
        sha=sha,
        short_sha=sha[:7],
        full_ref=branch,
        parent_shas=(parent,) if parent else (),
        github_author="example-user",
        git_author="Example Developer",
        authored_at=timestamp,
        committed_at=timestamp,
        message_subject=subject,
        url=f"https://github.example/repository/commit/{sha}",
    )


def test_one_commit_opens_one_session() -> None:
    service = FakeGithubService([raw_commit(SHA_1)])
    run = plan_github_project_memory(flow_input(), github_factory=lambda: service)

    assert run.status == "succeeded"
    assert run.result.status == "planned"
    assert run.result.verification == "not_applied"
    assert run.result.plan is not None
    assert len(run.result.plan.sessions) == 1
    assert run.result.plan.sessions[0].status == "open"


def test_continuous_commits_inside_window_share_session() -> None:
    first = datetime(2026, 7, 1, 9, tzinfo=UTC)
    service = FakeGithubService(
        [
            raw_commit(SHA_1, committed_at=first),
            raw_commit(SHA_2, parent=SHA_1, committed_at=first + timedelta(hours=2)),
        ]
    )
    run = plan_github_project_memory(flow_input(), github_factory=lambda: service)

    assert run.result.plan is not None
    assert len(run.result.plan.sessions) == 1
    assert run.result.plan.sessions[0].commit_ids == [
        f"{REPOSITORY_ID}:{SHA_1}",
        f"{REPOSITORY_ID}:{SHA_2}",
    ]


def test_commits_after_window_create_two_sessions_and_close_first() -> None:
    first = datetime(2026, 7, 1, 9, tzinfo=UTC)
    service = FakeGithubService(
        [
            raw_commit(SHA_1, committed_at=first),
            raw_commit(SHA_2, parent=SHA_1, committed_at=first + timedelta(hours=25)),
        ]
    )
    run = plan_github_project_memory(flow_input(), github_factory=lambda: service)

    assert run.result.plan is not None
    assert [session.status for session in run.result.plan.sessions] == ["closed", "open"]
    assert run.result.plan.sessions_closed == 1


def test_two_branches_create_distinct_sessions() -> None:
    commits = [
        normalized_commit(REPOSITORY_ID, SHA_1, branch="refs/heads/main"),
        normalized_commit(
            REPOSITORY_ID,
            SHA_2,
            branch="refs/heads/feature",
            parent=SHA_1,
        ),
    ]
    sessions, _, _ = group_development_sessions(commits, session_window_hours=24)
    assert len(sessions) == 2
    assert {session.primary_ref for session in sessions} == {
        "refs/heads/main",
        "refs/heads/feature",
    }


def test_two_repositories_never_share_session() -> None:
    commits = [
        normalized_commit(1, SHA_1),
        normalized_commit(2, SHA_2, parent=SHA_1),
    ]
    sessions, _, _ = group_development_sessions(commits, session_window_hours=24)
    assert len(sessions) == 2
    assert {session.repository_id for session in sessions} == {1, 2}


def test_title_is_not_an_identity_and_identical_run_is_stable() -> None:
    service = FakeGithubService([raw_commit(SHA_1, message="Title A")])
    first = plan_github_project_memory(flow_input(), github_factory=lambda: service)
    second = plan_github_project_memory(flow_input(), github_factory=lambda: service)
    assert first.result.plan is not None
    assert second.result.plan is not None
    first_session = first.result.plan.sessions[0]
    second_session = second.result.plan.sessions[0]

    assert first_session.computed_title == "main"
    assert first_session.session_id == second_session.session_id
    assert first_session.grouping_key == second_session.grouping_key
    assert first.result.plan.fingerprint == second.result.plan.fingerprint
    assert first.idempotency_key == second.idempotency_key


def test_commits_are_ordered_chronologically() -> None:
    early = datetime(2026, 7, 1, 9, tzinfo=UTC)
    commits = [
        normalized_commit(REPOSITORY_ID, SHA_2, parent=SHA_1, committed_at=early),
        normalized_commit(
            REPOSITORY_ID,
            SHA_1,
            committed_at=early - timedelta(hours=1),
        ),
    ]
    sessions, _, _ = group_development_sessions(commits, session_window_hours=24)
    assert sessions[0].commit_ids == [
        f"{REPOSITORY_ID}:{SHA_1}",
        f"{REPOSITORY_ID}:{SHA_2}",
    ]


def test_invalid_input_is_rejected_before_github_collection() -> None:
    service = FakeGithubService([raw_commit(SHA_1)])
    run = plan_github_project_memory(
        flow_input(allowed_repositories=()),
        github_factory=lambda: service,
    )
    assert run.status == "failed"
    assert run.errors[0].code == "repository_not_allowed"
    assert service.requests == []
    assert [step.step_id for step in run.step_results] == ["trigger"]


def test_empty_history_is_an_honest_skipped_plan() -> None:
    service = FakeGithubService([])
    run = plan_github_project_memory(flow_input(), github_factory=lambda: service)
    assert run.status == "skipped"
    assert run.result.status == "skipped"
    assert run.result.verification == "not_applied"
    assert run.result.resources_created == 0
    assert run.result.plan is not None
    assert [effect.effect_type for effect in run.result.effects] == ["no_change"]


def test_plan_has_no_notion_effect_and_metrics_are_coherent() -> None:
    service = FakeGithubService([raw_commit(SHA_1)])
    run = plan_github_project_memory(flow_input(), github_factory=lambda: service)
    assert run.result.plan is not None
    assert run.metrics["external_writes"] == 0
    assert run.metrics["commits_read"] == 1
    assert run.metrics["sessions"] == 1
    assert all("notion" not in effect.effect_type for effect in run.result.effects)
    assert [step.step_id for step in run.step_results] == [
        "trigger",
        "collect_github",
        "normalize",
        "validate",
        "group_sessions",
        "build_plan",
        "build_result",
    ]


def test_github_errors_are_structured() -> None:
    service = FakeGithubService([], error=GithubApiError("Dépôt introuvable."))
    run = plan_github_project_memory(flow_input(), github_factory=lambda: service)
    assert run.status == "failed"
    assert run.errors[0].code == "github_collection"
    assert run.errors[0].category == "connector"
    assert run.errors[0].message == "Dépôt introuvable."
    assert run.result.verification == "not_applied"


def test_github_authentication_errors_are_structured() -> None:
    service = FakeGithubService([], error=GithubAuthError("Token refusé."))
    run = plan_github_project_memory(flow_input(), github_factory=lambda: service)
    assert run.status == "failed"
    assert run.errors[0].code == "github_auth"
    assert run.errors[0].category == "authentication"


def test_invalid_timestamp_is_rejected_before_plan() -> None:
    invalid = raw_commit(SHA_1)
    invalid = GithubCommit(
        sha=invalid.sha,
        parent_shas=invalid.parent_shas,
        authored_at="2026-07-01T09:00:00",
        committed_at=invalid.committed_at,
        git_author=invalid.git_author,
        github_author=invalid.github_author,
        message=invalid.message,
        html_url=invalid.html_url,
    )
    run = plan_github_project_memory(
        flow_input(),
        github_factory=lambda: FakeGithubService([invalid]),
    )
    assert run.status == "failed"
    assert run.errors[0].code == "invalid_github_data"
    assert run.result.plan is None


def test_sensitive_commit_data_is_not_exposed() -> None:
    service = FakeGithubService(
        [
            raw_commit(
                SHA_1,
                message="Visible subject\nsecret@example.test token=do-not-expose",
            )
        ]
    )
    run = plan_github_project_memory(flow_input(), github_factory=lambda: service)
    assert run.result.plan is not None
    serialized = repr(run)
    assert "secret@example.test" not in serialized
    assert "do-not-expose" not in serialized
    assert "Visible subject" in serialized
