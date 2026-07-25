from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable

from hanuman.orchestrations.notion_markdown_sanitizer import (
    sanitize_markdown_for_notion,
)
from hanuman.orchestrations.obsidian_to_notion import (
    _notion_headers,
    build_notion_body,
    split_frontmatter,
)

MAX_CHILDREN_PER_REQUEST = 100


def _chunks(values: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _decode_http_error(exc: urllib.error.HTTPError) -> str:
    detail = exc.read().decode("utf-8", errors="replace")
    try:
        payload = json.loads(detail)
    except json.JSONDecodeError:
        return detail or str(exc)
    if isinstance(payload, dict):
        return str(payload.get("message") or payload.get("code") or payload)
    return str(payload)


def _request_json(url: str, method: str, body: Dict[str, Any]) -> Dict[str, Any]:
    request = urllib.request.Request(
        url=url,
        data=json.dumps(body).encode("utf-8"),
        headers=_notion_headers(),
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            loaded = json.loads(response.read().decode("utf-8"))
            if not isinstance(loaded, dict):
                raise RuntimeError("Réponse Notion inattendue.")
            return loaded
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Notion API {exc.code}: {_decode_http_error(exc)}") from exc


def _parent_mismatch(message: str) -> bool:
    lowered = message.lower()
    markers = (
        "database_id",
        "page_id",
        "parent should be",
        "parent type",
        "is a database",
        "is a page",
    )
    return any(marker in lowered for marker in markers)


def _create_page(body: Dict[str, Any]) -> Dict[str, Any]:
    children = list(body.get("children") or [])
    first_batch = children[:MAX_CHILDREN_PER_REQUEST]
    create_body = {**body, "children": first_batch}
    page = _request_json("https://api.notion.com/v1/pages", "POST", create_body)

    page_id = page.get("id")
    if not isinstance(page_id, str):
        raise RuntimeError("Notion a créé une page sans identifiant exploitable.")

    for batch in _chunks(children[MAX_CHILDREN_PER_REQUEST:], MAX_CHILDREN_PER_REQUEST):
        _request_json(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            "PATCH",
            {"children": batch},
        )
    return page


def send_markdown_to_notion_safe(
    markdown_path: str,
    parent_id: str,
    parent_is_db: bool | None = None,
    db_title_name: str = "Name",
) -> Dict[str, Any]:
    path = Path(markdown_path).expanduser().resolve()
    markdown = sanitize_markdown_for_notion(path.read_text(encoding="utf-8"))
    front, body_md = split_frontmatter(markdown)

    if parent_is_db is None:
        parent_is_db = False

    def make_body(as_database: bool) -> Dict[str, Any]:
        return build_notion_body(
            markdown_path=str(path),
            parent_id=parent_id,
            parent_is_db=as_database,
            front=front,
            body_md=body_md,
            db_title_name=db_title_name,
        )

    try:
        return _create_page(make_body(bool(parent_is_db)))
    except RuntimeError as first_error:
        if not _parent_mismatch(str(first_error)):
            raise
        try:
            return _create_page(make_body(not bool(parent_is_db)))
        except RuntimeError as second_error:
            raise RuntimeError(
                f"Échec avec le parent configuré puis avec le type alternatif. {second_error}"
            ) from second_error
