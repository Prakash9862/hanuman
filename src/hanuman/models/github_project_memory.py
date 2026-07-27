from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

StepStatus = Literal["succeeded", "failed", "skipped"]
RunStatus = Literal["succeeded", "failed", "skipped"]
SessionStatus = Literal["open", "closed"]
ContinuityStatus = Literal["confirmed", "unknown", "broken"]
SessionOpeningReason = Literal[
    "initial",
    "inactivity_window",
    "max_duration",
    "continuity_broken",
    "branch_change",
    "repository_change",
]


@dataclass(frozen=True)
class GitHubProjectMemoryInput:
    repository: str
    branch: str | None = None
    start_ref: str | None = None
    end_ref: str | None = None
    max_commits: int = 50
    session_window_hours: int = 24
    session_max_duration_hours: int = 12
    allowed_repositories: tuple[str, ...] = ()


@dataclass(frozen=True)
class NormalizedRepository:
    repository_id: int
    owner: str
    name: str
    full_name: str
    url: str
    default_branch: str


@dataclass(frozen=True)
class NormalizedCommit:
    repository_id: int
    sha: str
    short_sha: str
    full_ref: str
    parent_shas: tuple[str, ...]
    github_author: str | None
    git_author: str
    authored_at: datetime
    committed_at: datetime
    message_subject: str
    url: str
    provenance: str = "github"
    continuity_with_previous: ContinuityStatus | None = None

    @property
    def commit_id(self) -> str:
        return f"{self.repository_id}:{self.sha}"


@dataclass
class DevelopmentSession:
    session_id: str
    repository_id: int
    grouping_key: str
    grouping_version: int
    started_at: datetime
    last_activity_at: datetime
    ended_at: datetime | None
    commit_ids: list[str]
    branches: list[str]
    status: SessionStatus
    computed_title: str
    generated_summary: str
    github_links: list[str]
    primary_ref: str
    opening_reason: SessionOpeningReason
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PlannedEffect:
    effect_type: str
    identity: str
    description: str


@dataclass
class GitHubProjectMemoryPlan:
    schema_version: int
    repository: NormalizedRepository
    full_ref: str
    start_ref: str | None
    end_ref: str
    commits_read: int
    commits_valid: int
    commits_skipped: int
    commits: list[NormalizedCommit]
    sessions: list[DevelopmentSession]
    sessions_open: int
    sessions_closed: int
    commit_sessions: dict[str, str]
    effects: list[PlannedEffect]
    warnings: list[str]
    errors: list[StructuredError]
    metrics: dict[str, int | float]
    fingerprint: str


@dataclass(frozen=True)
class StructuredError:
    code: str
    category: str
    message: str
    retryable: bool = False


@dataclass
class StepResult:
    step_id: str
    status: StepStatus
    started_at: datetime
    finished_at: datetime
    input_refs: list[str] = field(default_factory=list)
    output_refs: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    metrics: dict[str, int | float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[StructuredError] = field(default_factory=list)


@dataclass
class FlowResult:
    status: Literal["planned", "skipped", "failed"]
    summary: str
    resources_read: int
    resources_created: int
    resources_updated: int
    resources_skipped: int
    resources_failed: int
    effects: list[PlannedEffect]
    warnings: list[str]
    verification: Literal["not_applied"]
    plan: GitHubProjectMemoryPlan | None = None


@dataclass
class FlowRun:
    run_id: str
    flow_id: str
    flow_version: str
    trigger: str
    status: RunStatus
    started_at: datetime
    finished_at: datetime
    input: dict[str, Any]
    step_results: list[StepResult]
    result: FlowResult
    errors: list[StructuredError]
    metrics: dict[str, int | float]
    idempotency_key: str
