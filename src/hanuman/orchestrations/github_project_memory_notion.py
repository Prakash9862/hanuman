from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, Callable

from hanuman.models.github_project_memory import (
    DevelopmentSession,
    FlowResult,
    FlowRun,
    GitHubProjectMemoryInput,
    GitHubProjectMemoryPlan,
    NormalizedCommit,
    PlannedEffect,
    StepResult,
    StructuredError,
)
from hanuman.orchestrations.github_project_memory import (
    GithubServiceFactory,
    plan_github_project_memory,
)
from hanuman.services.core.github_service import GithubService
from hanuman.services.core.notion_service import (
    NotionApiError,
    NotionAuthError,
    NotionDatabaseRef,
    NotionService,
)

NOTION_TEST_PARENT_PAGE_ID = "3aae48e88d808075a33ff7accbaf1a90"
REPOSITORIES_DATABASE_TITLE = "Repositories"
SESSIONS_DATABASE_TITLE = "Development Sessions"

NotionServiceFactory = Callable[[], NotionService]


@dataclass(frozen=True)
class DatabaseSnapshot:
    ref: NotionDatabaseRef
    database: dict[str, Any]
    data_source: dict[str, Any]
    created: bool


@dataclass(frozen=True)
class PageSnapshot:
    page: dict[str, Any]
    blocks: list[dict[str, Any]]
    expected_properties: dict[str, Any]
    expected_blocks: list[dict[str, Any]]
    identity: str
    resource_type: str
    created: bool


def _now() -> datetime:
    return datetime.now(UTC)


def _rich_text(content: str, *, url: str | None = None) -> list[dict[str, Any]]:
    text: dict[str, Any] = {"content": content}
    if url is not None:
        text["link"] = {"url": url}
    return [{"type": "text", "text": text}]


def _repository_schema() -> dict[str, Any]:
    return {
        "Name": {"title": {}},
        "GitHub Repository ID": {"number": {}},
        "Owner": {"rich_text": {}},
        "Repository": {"rich_text": {}},
        "Default Branch": {"rich_text": {}},
        "GitHub URL": {"url": {}},
        "Created At": {"date": {}},
        "Updated At": {"date": {}},
    }


def _session_schema(repository_data_source_id: str) -> dict[str, Any]:
    return {
        "Title": {"title": {}},
        "Session ID": {"rich_text": {}},
        "Repository": {
            "relation": {
                "data_source_id": repository_data_source_id,
                "single_property": {},
            }
        },
        "Grouping Key": {"rich_text": {}},
        "Grouping Version": {"number": {}},
        "Status": {"select": {"options": [{"name": "open"}, {"name": "closed"}]}},
        "Started At": {"date": {}},
        "Last Activity": {"date": {}},
        "Ended At": {"date": {}},
        "Commit Count": {"number": {}},
        "Opening Reason": {
            "select": {
                "options": [
                    {"name": "initial"},
                    {"name": "inactivity_window"},
                    {"name": "max_duration"},
                    {"name": "continuity_broken"},
                    {"name": "branch_change"},
                    {"name": "repository_change"},
                ]
            }
        },
        "Summary": {"rich_text": {}},
        "GitHub Branch": {"rich_text": {}},
        "GitHub URL": {"url": {}},
        "Created At": {"date": {}},
        "Updated At": {"date": {}},
    }


def _normalize_id(value: str) -> str:
    return value.replace("-", "").casefold()


def _plain_text(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in items:
        if "plain_text" in item:
            parts.append(str(item["plain_text"]))
        else:
            parts.append(str(item.get("text", {}).get("content", "")))
    return "".join(parts)


def _database_title(database: dict[str, Any]) -> str:
    title = _plain_text(database.get("title") or [])
    return title or str(database.get("name", ""))


def _database_ref(database: dict[str, Any]) -> NotionDatabaseRef:
    data_sources = database.get("data_sources") or []
    data_source_id = str(data_sources[0].get("id", "")) if data_sources else ""
    return NotionDatabaseRef(
        database_id=str(database.get("id", "")),
        data_source_id=data_source_id,
        url=str(database.get("url", "")),
    )


def _find_database(
    notion: NotionService,
    title: str,
) -> NotionDatabaseRef | None:
    results = notion.search(title, limit=100).get("results", [])
    matches: list[NotionDatabaseRef] = []
    for result in results:
        if _database_title(result) != title:
            continue
        if result.get("object") == "data_source":
            parent_page_id = str(result.get("database_parent", {}).get("page_id", ""))
            if _normalize_id(parent_page_id) != _normalize_id(NOTION_TEST_PARENT_PAGE_ID):
                continue
            matches.append(
                NotionDatabaseRef(
                    database_id=str(result.get("parent", {}).get("database_id", "")),
                    data_source_id=str(result.get("id", "")),
                    url=str(result.get("url", "")),
                )
            )
        elif result.get("object") == "database":
            parent_page_id = str(result.get("parent", {}).get("page_id", ""))
            if _normalize_id(parent_page_id) != _normalize_id(NOTION_TEST_PARENT_PAGE_ID):
                continue
            matches.append(_database_ref(result))
    if len(matches) > 1:
        raise NotionApiError(
            f"Plusieurs databases Notion '{title}' existent sous le parent de test."
        )
    return matches[0] if matches else None


def _ensure_database(
    notion: NotionService,
    *,
    title: str,
    schema: dict[str, Any],
) -> DatabaseSnapshot:
    ref = _find_database(notion, title)
    created = ref is None
    if ref is None:
        ref = notion.create_database(NOTION_TEST_PARENT_PAGE_ID, title, schema)
    database = notion.retrieve_database(ref.database_id)
    data_source = notion.retrieve_data_source(ref.data_source_id)
    return DatabaseSnapshot(
        ref=ref,
        database=database,
        data_source=data_source,
        created=created,
    )


def _repository_properties(plan: GitHubProjectMemoryPlan) -> dict[str, Any]:
    first_activity = min(commit.committed_at for commit in plan.commits)
    last_activity = max(commit.committed_at for commit in plan.commits)
    repository = plan.repository
    return {
        "Name": {"title": _rich_text(repository.full_name)},
        "GitHub Repository ID": {"number": repository.repository_id},
        "Owner": {"rich_text": _rich_text(repository.owner)},
        "Repository": {"rich_text": _rich_text(repository.name)},
        "Default Branch": {"rich_text": _rich_text(repository.default_branch)},
        "GitHub URL": {"url": repository.url},
        "Created At": {"date": {"start": _notion_date(first_activity)}},
        "Updated At": {"date": {"start": _notion_date(last_activity)}},
    }


def _notion_date(value: datetime) -> str:
    """Projette une date à la précision minute conservée par Notion."""
    return value.replace(second=0, microsecond=0).isoformat()


def _session_commits(
    session: DevelopmentSession,
    commits: list[NormalizedCommit],
) -> list[NormalizedCommit]:
    by_id = {commit.commit_id: commit for commit in commits}
    return [by_id[commit_id] for commit_id in session.commit_ids]


def _session_url(plan: GitHubProjectMemoryPlan, session: DevelopmentSession) -> str:
    branch = session.primary_ref.removeprefix("refs/heads/")
    return f"{plan.repository.url}/tree/{branch}"


def _session_properties(
    plan: GitHubProjectMemoryPlan,
    session: DevelopmentSession,
    repository_page_id: str,
) -> dict[str, Any]:
    return {
        "Title": {"title": _rich_text(session.computed_title)},
        "Session ID": {"rich_text": _rich_text(session.session_id)},
        "Repository": {"relation": [{"id": repository_page_id}]},
        "Grouping Key": {"rich_text": _rich_text(session.grouping_key)},
        "Grouping Version": {"number": session.grouping_version},
        "Status": {"select": {"name": session.status}},
        "Started At": {"date": {"start": _notion_date(session.started_at)}},
        "Last Activity": {"date": {"start": _notion_date(session.last_activity_at)}},
        "Ended At": {
            "date": (
                {"start": _notion_date(session.ended_at)} if session.ended_at is not None else None
            )
        },
        "Commit Count": {"number": len(session.commit_ids)},
        "Opening Reason": {"select": {"name": session.opening_reason}},
        "Summary": {"rich_text": _rich_text(session.generated_summary)},
        "GitHub Branch": {"rich_text": _rich_text(session.primary_ref)},
        "GitHub URL": {"url": _session_url(plan, session)},
        "Created At": {"date": {"start": _notion_date(session.started_at)}},
        "Updated At": {"date": {"start": _notion_date(session.last_activity_at)}},
    }


def _session_blocks(
    session: DevelopmentSession,
    commits: list[NormalizedCommit],
) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("Résumé")},
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(session.generated_summary)},
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("Commits")},
        },
    ]
    for commit in _session_commits(session, commits):
        author = commit.github_author or commit.git_author
        prefix = (
            f"{commit.short_sha} — {commit.committed_at.isoformat()} — "
            f"{author} — {commit.message_subject} — "
        )
        blocks.append(
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        *_rich_text(prefix),
                        *_rich_text("GitHub", url=commit.url),
                    ]
                },
            }
        )
    return blocks


def _query_by_number(
    notion: NotionService,
    database_id: str,
    property_name: str,
    value: int,
) -> list[dict[str, Any]]:
    return notion.query_database(
        database_id,
        filter_={"property": property_name, "number": {"equals": value}},
    )


def _query_by_text(
    notion: NotionService,
    database_id: str,
    property_name: str,
    value: str,
) -> list[dict[str, Any]]:
    return notion.query_database(
        database_id,
        filter_={"property": property_name, "rich_text": {"equals": value}},
    )


def _one_or_none(pages: list[dict[str, Any]], identity: str) -> dict[str, Any] | None:
    if len(pages) > 1:
        raise NotionApiError(f"Identité Notion dupliquée : {identity}.")
    return pages[0] if pages else None


def _property_value(value: dict[str, Any]) -> Any:
    property_type = value.get("type")
    if property_type in {"title", "rich_text"}:
        return _plain_text(value.get(property_type) or [])
    if property_type in {"number", "url"}:
        return value.get(property_type)
    if property_type == "date":
        date = value.get("date")
        return None if date is None else _canonical_date(str(date.get("start", "")))
    if property_type == "select":
        select = value.get("select")
        return None if select is None else select.get("name")
    if property_type == "relation":
        return sorted(
            _normalize_id(str(item.get("id", ""))) for item in value.get("relation") or []
        )
    raise ValueError(f"Type de propriété Notion non vérifiable : {property_type}.")


def _expected_property_value(value: dict[str, Any]) -> Any:
    if "title" in value:
        return _plain_text(value["title"])
    if "rich_text" in value:
        return _plain_text(value["rich_text"])
    if "number" in value:
        return value["number"]
    if "url" in value:
        return value["url"]
    if "date" in value:
        date = value["date"]
        return None if date is None else _canonical_date(str(date["start"]))
    if "select" in value:
        return value["select"]["name"]
    if "relation" in value:
        return sorted(_normalize_id(str(item["id"])) for item in value["relation"])
    raise ValueError("Propriété attendue non vérifiable.")


def _canonical_date(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(UTC).isoformat()


def _canonical_blocks(blocks: list[dict[str, Any]]) -> list[tuple[str, str, tuple[str, ...]]]:
    canonical: list[tuple[str, str, tuple[str, ...]]] = []
    for block in blocks:
        block_type = str(block.get("type", ""))
        rich_text = block.get(block_type, {}).get("rich_text") or []
        text = _plain_text(rich_text)
        urls: list[str] = []
        for item in rich_text:
            text_data = item.get("text") or {}
            link_data = text_data.get("link") or {}
            link = item.get("href") or link_data.get("url")
            if link:
                urls.append(str(link))
        canonical.append((block_type, text, tuple(urls)))
    return canonical


def _verify_database(
    snapshot: DatabaseSnapshot,
    *,
    title: str,
    schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    database = snapshot.database
    if _database_title(database) != title:
        errors.append(f"Database {title}: titre différent.")
    parent_id = str(database.get("parent", {}).get("page_id", ""))
    if _normalize_id(parent_id) != _normalize_id(NOTION_TEST_PARENT_PAGE_ID):
        errors.append(f"Database {title}: parent différent.")
    actual_properties = snapshot.data_source.get("properties") or {}
    for name, expected in schema.items():
        actual = actual_properties.get(name)
        expected_type = next(iter(expected))
        if actual is None or actual.get("type") != expected_type:
            errors.append(f"Database {title}: propriété {name} ({expected_type}) absente.")
    return errors


def _verify_page(snapshot: PageSnapshot) -> list[str]:
    errors: list[str] = []
    actual_properties = snapshot.page.get("properties") or {}
    for name, expected in snapshot.expected_properties.items():
        actual = actual_properties.get(name)
        if actual is None:
            errors.append(
                f"{snapshot.resource_type} {snapshot.identity}: propriété {name} absente."
            )
            continue
        actual_value = _property_value(actual)
        expected_value = _expected_property_value(expected)
        if actual_value != expected_value:
            errors.append(
                f"{snapshot.resource_type} {snapshot.identity}: propriété {name} différente "
                f"(reçu={actual_value!r}, attendu={expected_value!r})."
            )
    if _canonical_blocks(snapshot.blocks) != _canonical_blocks(snapshot.expected_blocks):
        errors.append(f"{snapshot.resource_type} {snapshot.identity}: contenu différent.")
    return errors


def _step(
    step_id: str,
    started_at: datetime,
    *,
    status: str = "succeeded",
    effects: list[str] | None = None,
    metrics: dict[str, int | float] | None = None,
    errors: list[StructuredError] | None = None,
) -> StepResult:
    return StepResult(
        step_id=step_id,
        status=status,  # type: ignore[arg-type]
        started_at=started_at,
        finished_at=_now(),
        effects=effects or [],
        metrics=metrics or {},
        errors=errors or [],
    )


def apply_github_project_memory(
    flow_input: GitHubProjectMemoryInput,
    *,
    github_factory: GithubServiceFactory = GithubService,
    notion_factory: NotionServiceFactory = NotionService,
) -> FlowRun:
    """Applique uniquement les créations Phase 2, puis vérifie chaque objet."""

    perf_started = perf_counter()
    planned_run = plan_github_project_memory(flow_input, github_factory=github_factory)
    if planned_run.result.plan is None or planned_run.status == "failed":
        return planned_run
    plan = planned_run.result.plan
    steps = list(planned_run.step_results)
    effects: list[PlannedEffect] = []
    page_snapshots: list[PageSnapshot] = []
    database_snapshots: list[tuple[DatabaseSnapshot, str, dict[str, Any]]] = []
    apply_started = _now()
    try:
        notion = notion_factory()
        repositories_database = _ensure_database(
            notion,
            title=REPOSITORIES_DATABASE_TITLE,
            schema=_repository_schema(),
        )
        database_snapshots.append(
            (repositories_database, REPOSITORIES_DATABASE_TITLE, _repository_schema())
        )
        sessions_schema = _session_schema(repositories_database.ref.data_source_id)
        sessions_database = _ensure_database(
            notion,
            title=SESSIONS_DATABASE_TITLE,
            schema=sessions_schema,
        )
        database_snapshots.append((sessions_database, SESSIONS_DATABASE_TITLE, sessions_schema))
        for snapshot, title, _ in database_snapshots:
            effects.append(
                PlannedEffect(
                    "database.create" if snapshot.created else "database.no_change",
                    snapshot.ref.database_id,
                    title,
                )
            )

        repository_properties = _repository_properties(plan)
        repository_page = _one_or_none(
            _query_by_number(
                notion,
                repositories_database.ref.database_id,
                "GitHub Repository ID",
                plan.repository.repository_id,
            ),
            f"repository:{plan.repository.repository_id}",
        )
        repository_created = repository_page is None
        if repository_page is None:
            ref = notion.create_page_in_data_source(
                repositories_database.ref.database_id,
                repository_properties,
            )
            repository_page = notion.retrieve_page(ref.page_id)
        repository_page_id = str(repository_page.get("id", ""))
        page_snapshots.append(
            PageSnapshot(
                page=repository_page,
                blocks=[],
                expected_properties=repository_properties,
                expected_blocks=[],
                identity=str(plan.repository.repository_id),
                resource_type="Repository",
                created=repository_created,
            )
        )
        effects.append(
            PlannedEffect(
                "repository.create" if repository_created else "repository.no_change",
                repository_page_id,
                plan.repository.full_name,
            )
        )

        for session in plan.sessions:
            properties = _session_properties(plan, session, repository_page_id)
            blocks = _session_blocks(session, plan.commits)
            session_page = _one_or_none(
                _query_by_text(
                    notion,
                    sessions_database.ref.database_id,
                    "Session ID",
                    session.session_id,
                ),
                f"session:{session.session_id}",
            )
            session_created = session_page is None
            if session_page is None:
                ref = notion.create_page_in_data_source(
                    sessions_database.ref.database_id,
                    properties,
                    blocks,
                )
                session_page = notion.retrieve_page(ref.page_id)
            session_page_id = str(session_page.get("id", ""))
            actual_blocks = notion.retrieve_block_children(session_page_id)
            page_snapshots.append(
                PageSnapshot(
                    page=session_page,
                    blocks=actual_blocks,
                    expected_properties=properties,
                    expected_blocks=blocks,
                    identity=session.session_id,
                    resource_type="Development Session",
                    created=session_created,
                )
            )
            effects.append(
                PlannedEffect(
                    (
                        "development_session.create"
                        if session_created
                        else "development_session.no_change"
                    ),
                    session_page_id,
                    session.computed_title,
                )
            )
    except (NotionAuthError, NotionApiError, ValueError) as exc:
        error = StructuredError("notion_apply", "connector", str(exc))
        steps.append(_step("apply_notion", apply_started, status="failed", errors=[error]))
        result = FlowResult(
            status="failed",
            summary=f"Apply Notion échoué : {exc}",
            resources_read=planned_run.result.resources_read,
            resources_created=0,
            resources_updated=0,
            resources_skipped=0,
            resources_failed=1,
            effects=effects,
            warnings=planned_run.result.warnings,
            verification="failed",
            plan=plan,
            verification_details=[str(exc)],
        )
        finished_at = _now()
        return FlowRun(
            run_id=planned_run.run_id,
            flow_id=planned_run.flow_id,
            flow_version=planned_run.flow_version,
            trigger=planned_run.trigger,
            status="failed",
            started_at=planned_run.started_at,
            finished_at=finished_at,
            input=planned_run.input,
            step_results=steps,
            result=result,
            errors=[error],
            metrics={
                **planned_run.metrics,
                "duration_ms": (perf_counter() - perf_started) * 1000,
                "external_writes": sum(
                    effect.effect_type.endswith(".create") for effect in effects
                ),
            },
            idempotency_key=planned_run.idempotency_key,
        )

    created_count = sum(effect.effect_type.endswith(".create") for effect in effects)
    no_change_count = sum(effect.effect_type.endswith(".no_change") for effect in effects)
    steps.append(
        _step(
            "apply_notion",
            apply_started,
            effects=[effect.effect_type for effect in effects],
            metrics={
                "resources_created": created_count,
                "resources_no_change": no_change_count,
                "resources_updated": 0,
                "resources_deleted": 0,
            },
        )
    )

    verify_started = _now()
    verification_errors: list[str] = []
    for database_snapshot, title, schema in database_snapshots:
        verification_errors.extend(_verify_database(database_snapshot, title=title, schema=schema))
    for page_snapshot in page_snapshots:
        verification_errors.extend(_verify_page(page_snapshot))
    verification_passed = not verification_errors
    structured_errors = [
        StructuredError("notion_verification", "verification", detail)
        for detail in verification_errors
    ]
    steps.append(
        _step(
            "verify_notion",
            verify_started,
            status="succeeded" if verification_passed else "failed",
            metrics={
                "resources_verified": len(database_snapshots) + len(page_snapshots),
                "verification_failures": len(verification_errors),
            },
            errors=structured_errors,
        )
    )

    finished_at = _now()
    result = FlowResult(
        status="verified" if verification_passed else "failed",
        summary=(
            f"{created_count} création(s), {no_change_count} sans changement ; "
            f"vérification {'réussie' if verification_passed else 'échouée'}."
        ),
        resources_read=planned_run.result.resources_read + len(page_snapshots),
        resources_created=created_count,
        resources_updated=0,
        resources_skipped=no_change_count,
        resources_failed=len(verification_errors),
        effects=effects,
        warnings=planned_run.result.warnings,
        verification="passed" if verification_passed else "failed",
        plan=plan,
        verification_details=verification_errors or ["Tous les objets correspondent au plan."],
    )
    metrics = {
        **planned_run.metrics,
        "duration_ms": (perf_counter() - perf_started) * 1000,
        "external_writes": created_count,
        "notion_databases_created": sum(
            effect.effect_type == "database.create" for effect in effects
        ),
        "notion_pages_created": sum(
            effect.effect_type in {"repository.create", "development_session.create"}
            for effect in effects
        ),
        "notion_no_change": no_change_count,
        "notion_updates": 0,
        "notion_deletions": 0,
        "resources_verified": len(database_snapshots) + len(page_snapshots),
    }
    return FlowRun(
        run_id=planned_run.run_id,
        flow_id=planned_run.flow_id,
        flow_version=planned_run.flow_version,
        trigger=planned_run.trigger,
        status="succeeded" if verification_passed else "failed",
        started_at=planned_run.started_at,
        finished_at=finished_at,
        input=planned_run.input,
        step_results=steps,
        result=result,
        errors=structured_errors,
        metrics=metrics,
        idempotency_key=planned_run.idempotency_key,
    )
