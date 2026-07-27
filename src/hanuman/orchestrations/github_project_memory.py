from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Any, Callable, Iterable

from hanuman.models.github_project_memory import (
    ContinuityStatus,
    DevelopmentSession,
    FlowResult,
    FlowRun,
    GitHubProjectMemoryInput,
    GitHubProjectMemoryPlan,
    NormalizedCommit,
    NormalizedRepository,
    PlannedEffect,
    SessionOpeningReason,
    StepResult,
    StructuredError,
)
from hanuman.services.core.github_service import (
    GithubApiError,
    GithubAuthError,
    GithubCommit,
    GithubRepo,
    GithubService,
)

FLOW_ID = "github-activity-notion-project-memory"
FLOW_VERSION = "1.0"
GROUPING_VERSION = 3
SESSION_NAMESPACE = uuid.UUID("b942def8-2247-59be-94bb-63d7b4def622")
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
CONVENTIONAL_SUBJECT = re.compile(
    r"^(?P<category>feat|fix|docs|test|tests|refactor|chore|style)"
    r"(?:\((?P<scope>[^)]+)\))?!?:\s*",
    re.IGNORECASE,
)
MAX_TITLE_LENGTH = 80
CATEGORY_LABELS = {
    "feat": "Fonctionnalités",
    "fix": "Corrections",
    "docs": "Documentation",
    "test": "Tests",
    "refactor": "Refactorisation",
    "chore": "Maintenance",
    "style": "Formatage",
}
SCOPE_LABELS = {
    "ui": "Interface",
    "flows": "Flux",
    "flow": "Flux",
    "cli": "CLI",
    "chess": "Échecs",
}

GithubServiceFactory = Callable[[], GithubService]


def _now() -> datetime:
    return datetime.now(UTC)


def _digest(payload: object) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _step(
    step_id: str,
    started_at: datetime,
    *,
    status: str = "succeeded",
    input_refs: Iterable[str] = (),
    output_refs: Iterable[str] = (),
    effects: Iterable[str] = (),
    metrics: dict[str, int | float] | None = None,
    warnings: Iterable[str] = (),
    errors: Iterable[StructuredError] = (),
) -> StepResult:
    return StepResult(
        step_id=step_id,
        status=status,  # type: ignore[arg-type]
        started_at=started_at,
        finished_at=_now(),
        input_refs=list(input_refs),
        output_refs=list(output_refs),
        effects=list(effects),
        metrics=metrics or {},
        warnings=list(warnings),
        errors=list(errors),
    )


def _parse_timestamp(value: str, field_name: str) -> datetime:
    if not value:
        raise ValueError(f"{field_name} est absent.")
    candidate = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(candidate)
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} doit contenir un fuseau horaire.")
    return parsed.astimezone(UTC)


def normalize_repository(repo: GithubRepo) -> NormalizedRepository:
    if repo.repository_id <= 0:
        raise ValueError("L'identité GitHub stable du dépôt est absente.")
    if not repo.owner or not repo.name or not repo.full_name:
        raise ValueError("La réponse GitHub du dépôt est incomplète.")
    if not repo.html_url or not repo.default_branch:
        raise ValueError("L'URL ou la branche par défaut du dépôt est absente.")
    return NormalizedRepository(
        repository_id=repo.repository_id,
        owner=repo.owner,
        name=repo.name,
        full_name=repo.full_name,
        url=repo.html_url,
        default_branch=repo.default_branch,
    )


def normalize_commit(
    raw: GithubCommit,
    *,
    repository_id: int,
    full_ref: str,
) -> NormalizedCommit:
    sha = raw.sha.lower()
    if not SHA_PATTERN.fullmatch(sha):
        raise ValueError("Le SHA du commit doit contenir 40 caractères hexadécimaux.")
    if not raw.git_author:
        raise ValueError(f"L'auteur Git du commit {sha} est absent.")
    if not raw.html_url:
        raise ValueError(f"L'URL GitHub du commit {sha} est absente.")
    message_subject = raw.message.splitlines()[0].strip() if raw.message else ""
    if not message_subject:
        raise ValueError(f"Le sujet du commit {sha} est absent.")
    return NormalizedCommit(
        repository_id=repository_id,
        sha=sha,
        short_sha=sha[:7],
        full_ref=full_ref,
        parent_shas=tuple(parent.lower() for parent in raw.parent_shas),
        github_author=raw.github_author,
        git_author=raw.git_author,
        authored_at=_parse_timestamp(raw.authored_at, "authored_at"),
        committed_at=_parse_timestamp(raw.committed_at, "committed_at"),
        message_subject=message_subject,
        url=raw.html_url,
    )


def _grouping_key(
    commit: NormalizedCommit,
    *,
    session_window_hours: int,
    session_max_duration_hours: int,
) -> str:
    return _digest(
        {
            "grouping_version": GROUPING_VERSION,
            "repository_id": commit.repository_id,
            "full_ref": commit.full_ref,
            "first_commit_sha": commit.sha,
            "session_window_hours": session_window_hours,
            "session_max_duration_hours": session_max_duration_hours,
        }
    )


def _session_id(grouping_key: str) -> str:
    return str(uuid.uuid5(SESSION_NAMESPACE, grouping_key))


def _ranked_themes(commits: list[NormalizedCommit]) -> list[str]:
    counts: dict[str, int] = {}
    first_seen: dict[str, int] = {}
    for index, commit in enumerate(commits):
        match = CONVENTIONAL_SUBJECT.match(commit.message_subject)
        if match is None:
            continue
        category = match.group("category").lower()
        if category == "tests":
            category = "test"
        category_label = CATEGORY_LABELS[category]
        counts[category_label] = counts.get(category_label, 0) + 1
        first_seen.setdefault(category_label, index)
        scope = (match.group("scope") or "").lower()
        scope_label = SCOPE_LABELS.get(scope)
        if scope_label is not None:
            counts[scope_label] = counts.get(scope_label, 0) + 1
            first_seen.setdefault(scope_label, index)
    return sorted(counts, key=lambda label: (-counts[label], first_seen[label], label))[:2]


def _computed_title(
    session: DevelopmentSession,
    commits: list[NormalizedCommit],
) -> str:
    branch = session.primary_ref.removeprefix("refs/heads/")
    session_ids = set(session.commit_ids)
    session_commits = [commit for commit in commits if commit.commit_id in session_ids]
    themes = _ranked_themes(session_commits)
    if themes:
        description = " et ".join(themes)
    else:
        description = f"Session du {session.started_at.date().isoformat()}"
    title = f"{branch} — {description}"
    if len(title) <= MAX_TITLE_LENGTH:
        return title
    return title[: MAX_TITLE_LENGTH - 1].rstrip() + "…"


def _summary(session: DevelopmentSession, commits: list[NormalizedCommit]) -> str:
    session_commits = [commit for commit in commits if commit.commit_id in set(session.commit_ids)]
    subjects = [commit.message_subject for commit in session_commits[:5]]
    suffix = "" if len(session_commits) <= 5 else f" ; +{len(session_commits) - 5} autre(s)"
    period = (
        f"{session.started_at.date().isoformat()} → "
        f"{session.last_activity_at.date().isoformat()}"
    )
    return (
        f"{len(session_commits)} commit(s), {period}, branche {session.primary_ref} : "
        f"{' ; '.join(subjects)}{suffix}"
    )


def _continuity(
    previous_sha: str,
    commit: NormalizedCommit,
) -> ContinuityStatus:
    if commit.continuity_with_previous is not None:
        return commit.continuity_with_previous
    if previous_sha in commit.parent_shas:
        return "confirmed"
    return "unknown"


def group_development_sessions(
    commits: list[NormalizedCommit],
    *,
    session_window_hours: int,
    session_max_duration_hours: int = 12,
) -> tuple[list[DevelopmentSession], dict[str, str], list[str], dict[str, int]]:
    """Regroupe des commits sans état persistant ni déduction probabiliste."""

    if session_window_hours < 1:
        raise ValueError("session_window_hours doit être supérieur ou égal à 1.")
    if session_max_duration_hours < 1:
        raise ValueError("session_max_duration_hours doit être supérieur ou égal à 1.")

    ordered = sorted(
        commits,
        key=lambda commit: (
            commit.committed_at,
            commit.repository_id,
            commit.full_ref,
            commit.sha,
        ),
    )
    sessions: list[DevelopmentSession] = []
    active: dict[tuple[int, str], DevelopmentSession] = {}
    associations: dict[str, str] = {}
    warnings: list[str] = []
    continuity_metrics = {
        "continuity_confirmed": 0,
        "continuity_unknown": 0,
        "continuity_broken": 0,
        "sessions_split_by_inactivity": 0,
        "sessions_split_by_max_duration": 0,
        "sessions_split_by_broken_continuity": 0,
        "sessions_split_by_branch_change": 0,
        "sessions_split_by_repository_change": 0,
    }
    window = timedelta(hours=session_window_hours)
    max_duration = timedelta(hours=session_max_duration_hours)
    seen_repositories: set[int] = set()
    seen_contexts: set[tuple[int, str]] = set()

    for commit in ordered:
        context = (commit.repository_id, commit.full_ref)
        current = active.get(context)
        opening_reason: SessionOpeningReason | None = None
        if current is not None:
            previous_sha = current.commit_ids[-1].split(":", maxsplit=1)[1]
            gap = commit.committed_at - current.last_activity_at
            continuity = _continuity(previous_sha, commit)
            continuity_metrics[f"continuity_{continuity}"] += 1
            if gap > window:
                current.status = "closed"
                current.ended_at = current.last_activity_at
                continuity_metrics["sessions_split_by_inactivity"] += 1
                opening_reason = "inactivity_window"
                current = None
            elif continuity == "broken":
                current.status = "closed"
                current.ended_at = current.last_activity_at
                continuity_metrics["sessions_split_by_broken_continuity"] += 1
                opening_reason = "continuity_broken"
                current = None
            elif commit.committed_at - current.started_at > max_duration:
                current.status = "closed"
                current.ended_at = current.last_activity_at
                continuity_metrics["sessions_split_by_max_duration"] += 1
                opening_reason = "max_duration"
                current = None
            elif continuity == "unknown":
                warning = (
                    f"Continuité Git non démontrée entre {previous_sha[:7]} et "
                    f"{commit.short_sha} ; regroupement temporel conservé."
                )
                warnings.append(warning)
                current.warnings.append(warning)

        if current is None:
            if opening_reason is None:
                if commit.repository_id not in seen_repositories and seen_repositories:
                    opening_reason = "repository_change"
                    continuity_metrics["sessions_split_by_repository_change"] += 1
                elif context not in seen_contexts and seen_contexts:
                    opening_reason = "branch_change"
                    continuity_metrics["sessions_split_by_branch_change"] += 1
                else:
                    opening_reason = "initial"
            grouping_key = _grouping_key(
                commit,
                session_window_hours=session_window_hours,
                session_max_duration_hours=session_max_duration_hours,
            )
            current = DevelopmentSession(
                session_id=_session_id(grouping_key),
                repository_id=commit.repository_id,
                grouping_key=grouping_key,
                grouping_version=GROUPING_VERSION,
                started_at=commit.committed_at,
                last_activity_at=commit.committed_at,
                ended_at=None,
                commit_ids=[],
                branches=[commit.full_ref],
                status="open",
                computed_title="",
                generated_summary="",
                github_links=[],
                primary_ref=commit.full_ref,
                opening_reason=opening_reason,
            )
            sessions.append(current)
            active[context] = current
            seen_repositories.add(commit.repository_id)
            seen_contexts.add(context)

        current.commit_ids.append(commit.commit_id)
        current.last_activity_at = commit.committed_at
        if commit.url not in current.github_links:
            current.github_links.append(commit.url)
        associations[commit.commit_id] = current.session_id

    for session in sessions:
        session.computed_title = _computed_title(session, ordered)
        session.generated_summary = _summary(session, ordered)
    return sessions, associations, warnings, continuity_metrics


def _plan_fingerprint_payload(
    repository: NormalizedRepository,
    full_ref: str,
    flow_input: GitHubProjectMemoryInput,
    commits: list[NormalizedCommit],
    sessions: list[DevelopmentSession],
    associations: dict[str, str],
) -> dict[str, Any]:
    return {
        "flow_id": FLOW_ID,
        "flow_version": FLOW_VERSION,
        "repository": asdict(repository),
        "full_ref": full_ref,
        "start_ref": flow_input.start_ref,
        "end_ref": flow_input.end_ref or full_ref,
        "max_commits": flow_input.max_commits,
        "session_window_hours": flow_input.session_window_hours,
        "session_max_duration_hours": flow_input.session_max_duration_hours,
        "commits": [asdict(commit) for commit in commits],
        "sessions": [asdict(session) for session in sessions],
        "associations": associations,
    }


def _failed_run(
    flow_input: GitHubProjectMemoryInput,
    started_at: datetime,
    step_results: list[StepResult],
    error: StructuredError,
    idempotency_key: str,
) -> FlowRun:
    finished_at = _now()
    result = FlowResult(
        status="failed",
        summary=error.message,
        resources_read=0,
        resources_created=0,
        resources_updated=0,
        resources_skipped=0,
        resources_failed=1,
        effects=[],
        warnings=[],
        verification="not_applied",
    )
    return FlowRun(
        run_id=str(uuid.uuid4()),
        flow_id=FLOW_ID,
        flow_version=FLOW_VERSION,
        trigger="cli.manual",
        status="failed",
        started_at=started_at,
        finished_at=finished_at,
        input=_safe_input(flow_input),
        step_results=step_results,
        result=result,
        errors=[error],
        metrics={"duration_ms": (finished_at - started_at).total_seconds() * 1000},
        idempotency_key=idempotency_key,
    )


def _safe_input(flow_input: GitHubProjectMemoryInput) -> dict[str, Any]:
    return {
        "repository": flow_input.repository,
        "branch": flow_input.branch,
        "start_ref": flow_input.start_ref,
        "end_ref": flow_input.end_ref,
        "max_commits": flow_input.max_commits,
        "session_window_hours": flow_input.session_window_hours,
        "session_max_duration_hours": flow_input.session_max_duration_hours,
    }


def _base_idempotency_key(flow_input: GitHubProjectMemoryInput) -> str:
    return _digest({"flow_id": FLOW_ID, "flow_version": FLOW_VERSION, **_safe_input(flow_input)})


def plan_github_project_memory(
    flow_input: GitHubProjectMemoryInput,
    *,
    github_factory: GithubServiceFactory = GithubService,
) -> FlowRun:
    """Calcule le plan Phase 1. Cette fonction ne connaît pas Notion."""

    run_started = _now()
    perf_started = perf_counter()
    steps: list[StepResult] = []
    idempotency_key = _base_idempotency_key(flow_input)

    trigger_started = _now()
    repository_name = flow_input.repository.strip()
    allowed = {name.casefold() for name in flow_input.allowed_repositories}
    input_error: StructuredError | None = None
    if not repository_name or repository_name.count("/") != 1:
        input_error = StructuredError(
            "invalid_repository", "validation", "Le dépôt doit suivre le format owner/name."
        )
    elif repository_name.casefold() not in allowed:
        input_error = StructuredError(
            "repository_not_allowed",
            "validation",
            f"Le dépôt {repository_name} n'est pas explicitement autorisé.",
        )
    elif flow_input.max_commits < 1 or flow_input.max_commits > 100:
        input_error = StructuredError(
            "invalid_max_commits",
            "validation",
            "max_commits doit être compris entre 1 et 100.",
        )
    elif flow_input.session_window_hours < 1:
        input_error = StructuredError(
            "invalid_session_window",
            "validation",
            "session_window_hours doit être supérieur ou égal à 1.",
        )
    elif flow_input.session_max_duration_hours < 1:
        input_error = StructuredError(
            "invalid_session_max_duration",
            "validation",
            "session_max_duration_hours doit être supérieur ou égal à 1.",
        )
    if input_error is not None:
        steps.append(_step("trigger", trigger_started, status="failed", errors=[input_error]))
        return _failed_run(flow_input, run_started, steps, input_error, idempotency_key)
    steps.append(
        _step(
            "trigger",
            trigger_started,
            input_refs=[repository_name],
            output_refs=["command:github-project-memory:plan"],
        )
    )

    collect_started = _now()
    try:
        github = github_factory()
        raw_repository = github.get_repo(repository_name)
        branch = flow_input.branch or raw_repository.default_branch
        full_ref = branch if branch.startswith("refs/") else f"refs/heads/{branch}"
        collection_ref = flow_input.end_ref or branch
        raw_commits = github.list_commits(
            repository_name,
            ref=collection_ref,
            start_sha=flow_input.start_ref,
            max_commits=flow_input.max_commits,
        )
    except GithubAuthError as exc:
        error = StructuredError("github_auth", "authentication", str(exc))
        steps.append(_step("collect_github", collect_started, status="failed", errors=[error]))
        return _failed_run(flow_input, run_started, steps, error, idempotency_key)
    except (GithubApiError, ValueError) as exc:
        error = StructuredError("github_collection", "connector", str(exc))
        steps.append(_step("collect_github", collect_started, status="failed", errors=[error]))
        return _failed_run(flow_input, run_started, steps, error, idempotency_key)
    steps.append(
        _step(
            "collect_github",
            collect_started,
            input_refs=[repository_name, collection_ref],
            output_refs=[commit.sha for commit in raw_commits],
            metrics={"commits_read": len(raw_commits)},
        )
    )

    normalize_started = _now()
    try:
        repository = normalize_repository(raw_repository)
        commits = [
            normalize_commit(
                raw_commit,
                repository_id=repository.repository_id,
                full_ref=full_ref,
            )
            for raw_commit in raw_commits
        ]
    except ValueError as exc:
        error = StructuredError("invalid_github_data", "validation", str(exc))
        steps.append(_step("normalize", normalize_started, status="failed", errors=[error]))
        return _failed_run(flow_input, run_started, steps, error, idempotency_key)
    steps.append(
        _step(
            "normalize",
            normalize_started,
            input_refs=[commit.sha for commit in raw_commits],
            output_refs=[commit.commit_id for commit in commits],
            metrics={"commits_normalized": len(commits)},
        )
    )

    validate_started = _now()
    duplicate_ids = len({commit.commit_id for commit in commits}) != len(commits)
    if duplicate_ids:
        error = StructuredError(
            "duplicate_commit", "validation", "La collecte contient un commit dupliqué."
        )
        steps.append(_step("validate", validate_started, status="failed", errors=[error]))
        return _failed_run(flow_input, run_started, steps, error, idempotency_key)
    steps.append(
        _step(
            "validate",
            validate_started,
            input_refs=[commit.commit_id for commit in commits],
            output_refs=[commit.commit_id for commit in commits],
            metrics={"commits_valid": len(commits), "commits_skipped": 0},
        )
    )

    group_started = _now()
    sessions, associations, warnings, continuity_metrics = group_development_sessions(
        commits,
        session_window_hours=flow_input.session_window_hours,
        session_max_duration_hours=flow_input.session_max_duration_hours,
    )
    steps.append(
        _step(
            "group_sessions",
            group_started,
            input_refs=[commit.commit_id for commit in commits],
            output_refs=[session.session_id for session in sessions],
            metrics={
                "sessions": len(sessions),
                "sessions_open": sum(session.status == "open" for session in sessions),
                "sessions_closed": sum(session.status == "closed" for session in sessions),
                **continuity_metrics,
            },
            warnings=warnings,
        )
    )

    plan_started = _now()
    effects: list[PlannedEffect]
    if commits:
        effects = [
            PlannedEffect(
                "repository.create",
                str(repository.repository_id),
                f"Projeter le dépôt {repository.full_name}.",
            ),
            *[
                PlannedEffect(
                    "development_session.create",
                    session.session_id,
                    f"Projeter {len(session.commit_ids)} commit(s) de {session.primary_ref}.",
                )
                for session in sessions
            ],
            *[
                PlannedEffect(
                    "development_session.close",
                    session.session_id,
                    "Clôturer la session à sa dernière activité.",
                )
                for session in sessions
                if session.status == "closed"
            ],
        ]
    else:
        effects = [
            PlannedEffect(
                "no_change",
                str(repository.repository_id),
                "Aucun commit dans la plage demandée ; aucune projection planifiée.",
            )
        ]

    fingerprint_payload = _plan_fingerprint_payload(
        repository, full_ref, flow_input, commits, sessions, associations
    )
    fingerprint = _digest(fingerprint_payload)
    idempotency_key = _digest(
        {
            "flow_id": FLOW_ID,
            "flow_version": FLOW_VERSION,
            "plan_fingerprint": fingerprint,
        }
    )
    plan = GitHubProjectMemoryPlan(
        schema_version=2,
        repository=repository,
        full_ref=full_ref,
        start_ref=flow_input.start_ref,
        end_ref=flow_input.end_ref or full_ref,
        commits_read=len(raw_commits),
        commits_valid=len(commits),
        commits_skipped=0,
        commits=commits,
        sessions=sessions,
        sessions_open=sum(session.status == "open" for session in sessions),
        sessions_closed=sum(session.status == "closed" for session in sessions),
        commit_sessions=associations,
        effects=effects,
        warnings=warnings,
        errors=[],
        metrics={
            "commits_read": len(raw_commits),
            "commits_valid": len(commits),
            "commits_skipped": 0,
            "sessions": len(sessions),
            **continuity_metrics,
        },
        fingerprint=fingerprint,
    )
    steps.append(
        _step(
            "build_plan",
            plan_started,
            input_refs=[session.session_id for session in sessions],
            output_refs=[fingerprint],
            effects=[effect.effect_type for effect in effects],
            metrics={"effects_planned": len(effects)},
        )
    )

    result_started = _now()
    empty = not commits
    result = FlowResult(
        status="skipped" if empty else "planned",
        summary=(
            "Aucun commit à planifier ; aucune écriture exécutée."
            if empty
            else f"{len(commits)} commit(s) regroupé(s) en {len(sessions)} session(s) ; "
            "aucune écriture exécutée."
        ),
        resources_read=1 + len(commits),
        resources_created=1 + len(sessions) if commits else 0,
        resources_updated=0,
        resources_skipped=1 if empty else 0,
        resources_failed=0,
        effects=effects,
        warnings=warnings,
        verification="not_applied",
        plan=plan,
    )
    steps.append(
        _step(
            "build_result",
            result_started,
            input_refs=[fingerprint],
            output_refs=[result.status],
            metrics={
                "resources_read": result.resources_read,
                "creations_planned": result.resources_created,
            },
        )
    )

    finished_at = _now()
    return FlowRun(
        run_id=str(uuid.uuid4()),
        flow_id=FLOW_ID,
        flow_version=FLOW_VERSION,
        trigger="cli.manual",
        status="skipped" if empty else "succeeded",
        started_at=run_started,
        finished_at=finished_at,
        input=_safe_input(flow_input),
        step_results=steps,
        result=result,
        errors=[],
        metrics={
            "duration_ms": (perf_counter() - perf_started) * 1000,
            "commits_read": len(raw_commits),
            "commits_valid": len(commits),
            "sessions": len(sessions),
            "sessions_open": plan.sessions_open,
            "sessions_closed": plan.sessions_closed,
            **continuity_metrics,
            "effects_planned": len(effects),
            "external_writes": 0,
        },
        idempotency_key=idempotency_key,
    )
