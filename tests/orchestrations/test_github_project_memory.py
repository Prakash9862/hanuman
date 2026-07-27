from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from hanuman.models.github_project_memory import (
    GitHubProjectMemoryInput,
    NormalizedCommit,
)
from hanuman.orchestrations.github_project_memory import (
    GROUPING_VERSION,
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
        "session_max_duration_hours": 12,
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
    continuity: str | None = None,
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
        continuity_with_previous=continuity,  # type: ignore[arg-type]
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
    assert run.metrics["continuity_confirmed"] == 1


def test_unknown_continuity_inside_window_keeps_session_with_warning() -> None:
    first = datetime(2026, 7, 1, 9, tzinfo=UTC)
    commits = [
        normalized_commit(REPOSITORY_ID, SHA_1, committed_at=first),
        normalized_commit(
            REPOSITORY_ID,
            SHA_2,
            committed_at=first + timedelta(minutes=10),
        ),
    ]

    sessions, _, warnings, metrics = group_development_sessions(commits, session_window_hours=24)

    assert len(sessions) == 1
    assert warnings == [
        f"Continuité Git non démontrée entre {SHA_1[:7]} et {SHA_2[:7]} ; "
        "regroupement temporel conservé."
    ]
    assert sessions[0].warnings == warnings
    assert metrics["continuity_unknown"] == 1


def test_explicitly_broken_continuity_inside_window_opens_session() -> None:
    first = datetime(2026, 7, 1, 9, tzinfo=UTC)
    commits = [
        normalized_commit(REPOSITORY_ID, SHA_1, committed_at=first),
        normalized_commit(
            REPOSITORY_ID,
            SHA_2,
            committed_at=first + timedelta(minutes=10),
            continuity="broken",
        ),
    ]

    sessions, _, warnings, metrics = group_development_sessions(commits, session_window_hours=24)

    assert [session.status for session in sessions] == ["closed", "open"]
    assert warnings == []
    assert metrics["continuity_broken"] == 1
    assert metrics["sessions_split_by_broken_continuity"] == 1


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
    assert run.metrics["sessions_split_by_inactivity"] == 1


def test_confirmed_continuity_does_not_bypass_max_duration() -> None:
    first = datetime(2026, 7, 1, 9, tzinfo=UTC)
    commits = [
        normalized_commit(REPOSITORY_ID, SHA_1, committed_at=first),
        normalized_commit(
            REPOSITORY_ID,
            SHA_2,
            parent=SHA_1,
            committed_at=first + timedelta(hours=12, seconds=1),
        ),
    ]

    sessions, _, _, metrics = group_development_sessions(
        commits,
        session_window_hours=24,
        session_max_duration_hours=12,
    )

    assert [session.opening_reason for session in sessions] == ["initial", "max_duration"]
    assert [session.status for session in sessions] == ["closed", "open"]
    assert metrics["sessions_split_by_max_duration"] == 1


def test_session_is_not_split_at_max_duration_limit() -> None:
    first = datetime(2026, 7, 1, 9, tzinfo=UTC)
    commits = [
        normalized_commit(REPOSITORY_ID, SHA_1, committed_at=first),
        normalized_commit(
            REPOSITORY_ID,
            SHA_2,
            parent=SHA_1,
            committed_at=first + timedelta(hours=12),
        ),
    ]

    sessions, _, _, metrics = group_development_sessions(
        commits,
        session_window_hours=24,
        session_max_duration_hours=12,
    )

    assert len(sessions) == 1
    assert metrics["sessions_split_by_max_duration"] == 0


def test_unknown_continuity_is_kept_before_max_duration() -> None:
    first = datetime(2026, 7, 1, 9, tzinfo=UTC)
    commits = [
        normalized_commit(REPOSITORY_ID, SHA_1, committed_at=first),
        normalized_commit(
            REPOSITORY_ID,
            SHA_2,
            committed_at=first + timedelta(hours=11),
        ),
    ]

    sessions, _, warnings, _ = group_development_sessions(
        commits,
        session_window_hours=24,
        session_max_duration_hours=12,
    )

    assert len(sessions) == 1
    assert len(warnings) == 1


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
    sessions, _, _, _ = group_development_sessions(commits, session_window_hours=24)
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
    sessions, _, _, _ = group_development_sessions(commits, session_window_hours=24)
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

    assert first_session.computed_title == "main — Session du 2026-07-01"
    assert first_session.grouping_version == GROUPING_VERSION == 3
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
    sessions, _, _, _ = group_development_sessions(commits, session_window_hours=24)
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


def test_invalid_temporal_parameters_are_rejected_before_collection() -> None:
    service = FakeGithubService([raw_commit(SHA_1)])

    invalid_window = plan_github_project_memory(
        flow_input(session_window_hours=0),
        github_factory=lambda: service,
    )
    invalid_duration = plan_github_project_memory(
        flow_input(session_max_duration_hours=0),
        github_factory=lambda: service,
    )

    assert invalid_window.errors[0].code == "invalid_session_window"
    assert invalid_duration.errors[0].code == "invalid_session_max_duration"
    assert service.requests == []


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


def test_computed_title_uses_multiple_commits_and_is_bounded() -> None:
    first = datetime(2026, 7, 1, 9, tzinfo=UTC)
    service = FakeGithubService(
        [
            raw_commit(SHA_1, committed_at=first, message="docs: architecture"),
            raw_commit(
                SHA_2,
                parent=SHA_1,
                committed_at=first + timedelta(minutes=1),
                message="test: orchestrations",
            ),
            raw_commit(
                SHA_3,
                parent=SHA_2,
                committed_at=first + timedelta(minutes=2),
                message="docs: migration",
            ),
        ]
    )
    run = plan_github_project_memory(flow_input(), github_factory=lambda: service)

    assert run.result.plan is not None
    title = run.result.plan.sessions[0].computed_title
    assert title == "main — Documentation"
    assert len(title) <= 80


def test_title_fallback_by_date_is_deterministic() -> None:
    service = FakeGithubService([raw_commit(SHA_1, message="Merge branch feature/example")])
    first = plan_github_project_memory(flow_input(), github_factory=lambda: service)
    second = plan_github_project_memory(flow_input(), github_factory=lambda: service)

    assert first.result.plan is not None
    assert second.result.plan is not None
    assert first.result.plan.sessions[0].computed_title == "main — Session du 2026-07-01"
    assert (
        first.result.plan.sessions[0].computed_title
        == second.result.plan.sessions[0].computed_title
    )


def test_grouping_version_is_part_of_grouping_key(
    monkeypatch: Any,
) -> None:
    import hanuman.orchestrations.github_project_memory as project_memory

    commits = [normalized_commit(REPOSITORY_ID, SHA_1)]
    current, _, _, _ = group_development_sessions(commits, session_window_hours=24)
    monkeypatch.setattr(project_memory, "GROUPING_VERSION", GROUPING_VERSION + 1)
    next_version, _, _, _ = group_development_sessions(commits, session_window_hours=24)

    assert current[0].grouping_key != next_version[0].grouping_key
    assert current[0].session_id != next_version[0].session_id


def test_temporal_configuration_is_part_of_grouping_identity() -> None:
    commits = [normalized_commit(REPOSITORY_ID, SHA_1)]
    short, _, _, _ = group_development_sessions(
        commits,
        session_window_hours=24,
        session_max_duration_hours=12,
    )
    long, _, _, _ = group_development_sessions(
        commits,
        session_window_hours=24,
        session_max_duration_hours=24,
    )
    narrow_window, _, _, _ = group_development_sessions(
        commits,
        session_window_hours=12,
        session_max_duration_hours=12,
    )

    assert short[0].grouping_key != long[0].grouping_key
    assert short[0].session_id != long[0].session_id
    assert short[0].grouping_key != narrow_window[0].grouping_key
    assert short[0].session_id != narrow_window[0].session_id


def test_real_unknown_continuity_pattern_no_longer_creates_unit_sessions() -> None:
    start = datetime(2026, 7, 1, 8, tzinfo=UTC)
    commits: list[NormalizedCommit] = []
    previous: str | None = None
    for index in range(50):
        sha = f"{index + 1:040x}"
        parent = previous if index < 32 or index >= 37 else None
        commits.append(
            normalized_commit(
                REPOSITORY_ID,
                sha,
                parent=parent,
                committed_at=start + timedelta(minutes=index * 30),
                subject=f"docs: change {index + 1}",
            )
        )
        previous = sha

    sessions, _, warnings, metrics = group_development_sessions(commits, session_window_hours=24)

    distribution = [len(session.commit_ids) for session in sessions]
    assert 1 < len(sessions) < 7
    assert min(distribution) > 1
    assert max(session.last_activity_at - session.started_at for session in sessions) <= timedelta(
        hours=12
    )
    assert len(warnings) == 5
    assert metrics["continuity_confirmed"] == 44
    assert metrics["continuity_unknown"] == 5
    assert metrics["continuity_broken"] == 0
    assert metrics["sessions_split_by_max_duration"] == len(sessions) - 1
