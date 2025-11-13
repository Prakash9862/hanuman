from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

import yaml

# ========================
# Front-matter & Markdown
# ========================


@dataclass
class FrontMatter:
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    date: Optional[str] = None
    props: Optional[Dict[str, Any]] = None  # reste des champs

    def __post_init__(self) -> None:
        if self.props is None:
            self.props = {}


FM_RE = re.compile(r"^\s*---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def split_frontmatter(text: str) -> Tuple[FrontMatter, str]:
    """
    Extrait un front-matter YAML '--- ... ---' s'il existe, sinon renvoie vide.
    """
    m = FM_RE.match(text)
    if not m:
        return FrontMatter(), text

    raw = m.group(1)
    body = text[m.end() :]

    fm: Dict[str, Any] = {}
    if yaml:
        try:
            loaded = yaml.safe_load(raw) or {}
            if isinstance(loaded, dict):
                fm = loaded
        except Exception:
            fm = {}
    else:
        # Fallback ultra simple: lignes "key: value" + tags basiques
        fm = {}
        for line in raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()

        # listes type "tags: [a, b]" naïf
        if "tags" in fm and isinstance(fm["tags"], str):
            s = fm["tags"].strip()
            if s.startswith("[") and s.endswith("]"):
                fm["tags"] = [x.strip() for x in s[1:-1].split(",") if x.strip()]

    return normalize_frontmatter(fm), body


def normalize_frontmatter(fm: Dict[str, Any]) -> FrontMatter:
    title = fm.get("title") or fm.get("name") or None
    summary = fm.get("summary") or fm.get("description") or None
    tags = None
    if "tags" in fm:
        if isinstance(fm["tags"], list):
            tags = [str(t) for t in fm["tags"]]
        elif isinstance(fm["tags"], str):
            tags = [t.strip() for t in fm["tags"].split(",") if t.strip()]
    date = fm.get("date") or fm.get("created") or None
    # retire champs connus
    props = {
        k: v
        for k, v in fm.items()
        if k
        not in {"title", "name", "summary", "description", "tags", "date", "created"}
    }
    return FrontMatter(
        title=title,
        summary=summary,
        tags=tags,
        date=str(date) if date else None,
        props=props,
    )


# ============
# Notion utils
# ============


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


def _post_create_page(body: Dict[str, Any]) -> Dict[str, Any]:
    req = urllib.request.Request(
        url="https://api.notion.com/v1/pages",
        data=json.dumps(body).encode("utf-8"),
        headers=_notion_headers(),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        loaded = json.loads(resp.read().decode("utf-8"))
        return cast(Dict[str, Any], loaded)


# --- PATCH: helpers Notion avec chunking 2000 chars ---

MAX_CHUNK = 2000  # limite Notion


def _chunks(s: str, n: int = MAX_CHUNK) -> list[str]:
    if not s:
        return []
    return [s[i : i + n] for i in range(0, len(s), n)]


def _rich(text: str) -> list[dict]:
    """Découpe le texte long en morceaux de ≤2000 caractères."""
    return [
        {"type": "text", "text": {"content": part}} for part in _chunks(text, MAX_CHUNK)
    ]


def _code_block(code: str, language: str = "") -> dict:
    """Block de code compatible Notion (chunké)."""
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": _rich(code),
            "language": (language or "plain text"),
        },
    }


# ======================
# Markdown → Notion v2
# ======================

CODE_FENCE_RE = re.compile(r"^```(\w+)?\s*$")
HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")
ORDERED_RE = re.compile(r"^\s*\d+\.\s+(.*)$")
UNORDERED_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
BLOCKQUOTE_RE = re.compile(r"^\s*>\s+(.*)$")


def md_to_blocks(md: str) -> List[Dict[str, Any]]:
    """
    Convertit un markdown simple en blocks Notion (headings, lists, quotes, code, paragraphs).
    """
    lines = md.replace("\r\n", "\n").split("\n")
    blocks: List[Dict[str, Any]] = []
    in_code = False
    code_lang = ""
    code_buf: List[str] = []
    list_buffer: List[Tuple[str, bool]] = []  # (text, ordered)

    def flush_code() -> None:
        nonlocal code_buf, code_lang, in_code
        if code_buf:
            blocks.append(_code_block("\n".join(code_buf), code_lang))
        code_buf, code_lang, in_code = [], "", False

    def flush_list() -> None:
        nonlocal list_buffer
        for text, ordered in list_buffer:
            if ordered:
                blocks.append(
                    {
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {"rich_text": _rich(text)},
                    }
                )
            else:
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": _rich(text)},
                    }
                )
        list_buffer = []

    for raw in lines:
        # code fences
        m_code = CODE_FENCE_RE.match(raw)
        if m_code:
            if not in_code:
                flush_list()
                in_code = True
                code_lang = (m_code.group(1) or "").lower()
                code_buf = []
            else:
                flush_code()
            continue

        if in_code:
            code_buf.append(raw)
            continue

        # blank line → flush lists
        if raw.strip() == "":
            flush_list()
            continue

        # headings
        m_h = HEADING_RE.match(raw)
        if m_h:
            flush_list()
            level = len(m_h.group(1))
            text = m_h.group(2).strip()
            hkey = {1: "heading_1", 2: "heading_2", 3: "heading_3"}[min(level, 3)]
            blocks.append(
                {"object": "block", "type": hkey, hkey: {"rich_text": _rich(text)}}
            )
            continue

        # lists
        m_o = ORDERED_RE.match(raw)
        if m_o:
            list_buffer.append((m_o.group(1).strip(), True))
            continue

        m_u = UNORDERED_RE.match(raw)
        if m_u:
            list_buffer.append((m_u.group(1).strip(), False))
            continue

        # blockquote
        m_q = BLOCKQUOTE_RE.match(raw)
        if m_q:
            flush_list()
            blocks.append(
                {
                    "object": "block",
                    "type": "quote",
                    "quote": {"rich_text": _rich(m_q.group(1).strip())},
                }
            )
            continue

        # paragraph
        flush_list()
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": _rich(raw)},
            }
        )

    # fin
    if in_code:
        flush_code()
    else:
        flush_list()

    return blocks


# ============================
# Build Notion body (v2)
# ============================


def build_notion_body(
    path: str,
    parent_id: str,
    parent_is_db: bool,
    front: FrontMatter,
    md_body: str,
    *,
    db_title_name: str = "Name",
    db_tags_name: str = "Tags",
    db_summary_name: str = "Summary",
    db_date_name: str = "Date",
) -> Dict[str, Any]:
    title = front.title or Path(path).stem
    children = md_to_blocks(md_body)

    if parent_is_db:
        # Database parent: on mappe vers des propriétés
        props: Dict[str, Any] = {
            db_title_name: {"title": _rich(title)},
        }
        if front.summary:
            props[db_summary_name] = {"rich_text": _rich(front.summary)}
        if front.tags:
            props[db_tags_name] = {"multi_select": [{"name": t} for t in front.tags]}
        if front.date:
            props[db_date_name] = {"date": {"start": front.date}}

        # autres props scalaires simples
        for k, v in (front.props or {}).items():
            if isinstance(v, str):
                props[k] = {"rich_text": _rich(v)}
            elif isinstance(v, (int, float)):
                props[k] = {"number": v}
            elif isinstance(v, list):
                # on tente en multi_select de noms
                props[k] = {"multi_select": [{"name": str(x)} for x in v]}
            # sinon on ignore poliment

        body = {
            "parent": {"type": "database_id", "database_id": parent_id},
            "properties": props,
            "children": children,
        }
    else:
        # Page parent: seule prop 'title', le reste vit dans les blocks
        body = {
            "parent": {"type": "page_id", "page_id": parent_id},
            "properties": {"title": _rich(title)},
            "children": children
            if children
            else [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": _rich("")},
                }
            ],
        }

        # Ajoute un callout résumant le front-matter si utile
        meta_lines = []
        if front.summary:
            meta_lines.append(f"Résumé: {front.summary}")
        if front.tags:
            meta_lines.append("Tags: " + ", ".join(front.tags))
        if front.date:
            meta_lines.append(f"Date: {front.date}")
        for k, v in (front.props or {}).items():
            meta_lines.append(f"{k}: {v}")
        if meta_lines:
            callout_block: Dict[str, Any] = {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": _rich("\n".join(meta_lines)),
                    "icon": {"type": "emoji", "emoji": "🗂️"},
                },
            }
            existing_children = cast(List[Dict[str, Any]], body.get("children", []))
            body["children"] = [callout_block, *existing_children]

    return body


# ============================
# Orchestration (public API)
# ============================


def _read_markdown(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Markdown introuvable: {p}")
    return p.read_text(encoding="utf-8")


def send_markdown_to_notion(
    path: str,
    parent_id: str,
    parent_is_db: bool | None = None,
    db_title_name: str = "Name",
    db_tags_name: str = "Tags",
    db_summary_name: str = "Summary",
    db_date_name: str = "Date",
) -> Dict[str, Any]:
    md = _read_markdown(path)
    front, body_md = split_frontmatter(md)

    # déduction du type parent si non fourni
    if parent_is_db is None:
        env_flag = os.environ.get("NOTION_PARENT_IS_DB", "").strip().lower()
        parent_is_db = env_flag in ("1", "true", "yes", "y")

    body = build_notion_body(
        path=path,
        parent_id=parent_id,
        parent_is_db=bool(parent_is_db),
        front=front,
        md_body=body_md,
        db_title_name=db_title_name or os.environ.get("NOTION_DB_TITLE_NAME", "Name"),
        db_tags_name=db_tags_name or os.environ.get("NOTION_DB_TAGS_NAME", "Tags"),
        db_summary_name=db_summary_name
        or os.environ.get("NOTION_DB_SUMMARY_NAME", "Summary"),
        db_date_name=db_date_name or os.environ.get("NOTION_DB_DATE_NAME", "Date"),
    )

    try:
        return _post_create_page(body)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        # auto-retry: inverse page<->database sur 400 de validation
        if e.code == 400 and (
            "Invalid property" in detail or "validation_error" in detail
        ):
            body_alt = build_notion_body(
                path=path,
                parent_id=parent_id,
                parent_is_db=not bool(parent_is_db),
                front=front,
                md_body=body_md,
            )
            try:
                return _post_create_page(body_alt)
            except urllib.error.HTTPError as e2:
                raise RuntimeError(
                    f"Notion API error {e2.code}: {e2.read().decode('utf-8', 'ignore')}"
                ) from e2
        raise RuntimeError(f"Notion API error {e.code}: {detail}") from e


# =========
# CLI v2
# =========
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push Obsidian MD to Notion (v2: front-matter & markdown blocks)"
    )
    parser.add_argument("--path", required=True, help="Chemin du fichier .md")
    parser.add_argument(
        "--parent-id",
        default=os.environ.get("NOTION_PARENT_PAGE_ID")
        or os.environ.get("NOTION_PARENT_ID")
        or "",
        help="ID de la page ou base Notion parent",
    )
    parser.add_argument(
        "--parent-is-db",
        action="store_true",
        help="Indique que le parent est une **base** Notion",
    )
    parser.add_argument(
        "--db-title-name", default=os.environ.get("NOTION_DB_TITLE_NAME", "Name")
    )
    parser.add_argument(
        "--db-tags-name", default=os.environ.get("NOTION_DB_TAGS_NAME", "Tags")
    )
    parser.add_argument(
        "--db-summary-name", default=os.environ.get("NOTION_DB_SUMMARY_NAME", "Summary")
    )
    parser.add_argument(
        "--db-date-name", default=os.environ.get("NOTION_DB_DATE_NAME", "Date")
    )
    args = parser.parse_args()

    if not args.parent_id:
        raise SystemExit(
            "Parent Notion manquant (NOTION_PARENT_PAGE_ID/NOTION_PARENT_ID ou --parent-id)"
        )

    out = send_markdown_to_notion(
        path=args.path,
        parent_id=args.parent_id,
        parent_is_db=args.parent_is_db,
        db_title_name=args.db_title_name,
        db_tags_name=args.db_tags_name,
        db_summary_name=args.db_summary_name,
        db_date_name=args.db_date_name,
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
