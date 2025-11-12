from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List
import urllib.request
import urllib.error


def _read_markdown(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Markdown introuvable: {p}")
    return p.read_text(encoding="utf-8")


def _notion_headers() -> Dict[str, str]:
    token = os.environ.get("NOTION_TOKEN")
    version = os.environ.get("NOTION_VERSION", "2025-09-03")
    if not token:
        raise RuntimeError("NOTION_TOKEN manquant dans l'environnement")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": version,
        "Content-Type": "application/json",
    }


def _build_children_from_markdown(md: str) -> List[Dict[str, Any]]:
    # Simplifié : tout le contenu du Markdown dans un paragraphe unique
    return [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": md[:2000]}}],
            },
        }
    ]


def _properties_for_page_title(title: str) -> Dict[str, Any]:
    return {"title": [{"type": "text", "text": {"content": title}}]}


def _properties_for_database_title(title: str, db_title_name: str = "Name") -> Dict[str, Any]:
    return {db_title_name: {"title": [{"type": "text", "text": {"content": title}}]}}


def _post_create_page(body: Dict[str, Any]) -> Dict[str, Any]:
    req = urllib.request.Request(
        url="https://api.notion.com/v1/pages",
        data=json.dumps(body).encode("utf-8"),
        headers=_notion_headers(),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_markdown_to_notion(
    path: str,
    parent_id: str,
    parent_is_db: bool | None = None,
    db_title_name: str = "Name",
) -> Dict[str, Any]:
    """
    Crée une page dans Notion à partir d’un fichier Markdown.
    Gère automatiquement les cas page vs base (retry sur 400).
    """
    title = Path(path).stem
    md = _read_markdown(path)
    children = _build_children_from_markdown(md)

    if parent_is_db is None:
        env_flag = os.environ.get("NOTION_PARENT_IS_DB", "").strip().lower()
        parent_is_db = env_flag in ("1", "true", "yes", "y")

    def _body(is_db: bool) -> Dict[str, Any]:
        props = (
            _properties_for_database_title(title, db_title_name)
            if is_db
            else _properties_for_page_title(title)
        )
        parent = (
            {"type": "database_id", "database_id": parent_id}
            if is_db
            else {"type": "page_id", "page_id": parent_id}
        )
        return {"parent": parent, "properties": props, "children": children}

    try:
        return _post_create_page(_body(parent_is_db))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        if e.code == 400 and ("Invalid property" in detail or "validation_error" in detail):
            # tente automatiquement le mode inverse
            return _post_create_page(_body(not parent_is_db))
        raise RuntimeError(f"Notion API error {e.code}: {detail}") from e


def main() -> None:
    parser = argparse.ArgumentParser(description="Push Obsidian MD to Notion")
    parser.add_argument("--path", required=True, help="Chemin du fichier .md")
    parser.add_argument(
        "--parent-id",
        default=os.environ.get("NOTION_PARENT_PAGE_ID")
        or os.environ.get("NOTION_PARENT_ID")
        or "",
        help="Page ou base Notion parent",
    )
    parser.add_argument("--parent-is-db", action="store_true", help="Indique si le parent est une base Notion")
    parser.add_argument("--db-title-name", default="Name", help="Nom de la propriété titre de la base (défaut: Name)")
    args = parser.parse_args()

    if not args.parent_id:
        raise SystemExit("Parent Notion manquant (NOTION_PARENT_PAGE_ID ou --parent-id)")

    out = send_markdown_to_notion(
        path=args.path,
        parent_id=args.parent_id,
        parent_is_db=args.parent_is_db,
        db_title_name=args.db_title_name,
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
