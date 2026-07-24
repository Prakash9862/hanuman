# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List

OBSIDIAN_VAULT = Path(
    os.getenv("OBSIDIAN_VAULT_PATH")
    or os.getenv("OBSIDIAN_VAULT_DIR")
    or os.path.expanduser("~/Prakash/obsidian")
).expanduser()


def abs_path(rel_or_abs: str) -> Path:
    path = Path(rel_or_abs).expanduser()
    return path if path.is_absolute() else OBSIDIAN_VAULT / path


def read_markdown(path: str) -> str:
    p = abs_path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Markdown introuvable: {p}")
    return p.read_text(encoding="utf-8", errors="replace")


def _chunks(s: str, n: int = 1800):
    for i in range(0, len(s), n):
        yield s[i : i + n]


def md_to_blocks(md: str) -> List[Dict[str, Any]]:
    """Parse sobre et robuste: H1→titre de page, H2/H3, listes, paragraphes (avec découpe)."""
    blocks: List[Dict[str, Any]] = []
    lines = md.splitlines()

    def t(s: str) -> Dict[str, Any]:
        return {"type": "text", "text": {"content": s}}

    for raw in lines:
        line = raw.rstrip()
        if line.strip() == "":
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}})
            continue
        if line.startswith("### "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": [t(line[4:].strip())]},
                }
            )
            continue
        if line.startswith("## "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [t(line[3:].strip())]},
                }
            )
            continue
        if line.startswith("# "):
            # on saute: ce H1 servira de titre (géré dans le service Notion)
            continue
        if re.match(r"^\s*[-*]\s+", line):
            val = re.sub(r"^\s*[-*]\s+", "", line).strip()
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [t(val)]},
                }
            )
            continue
        if re.match(r"^\s*\d+\.\s+", line):
            val = re.sub(r"^\s*\d+\.\s+", "", line).strip()
            blocks.append(
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [t(val)]},
                }
            )
            continue
        for part in _chunks(line, 1800):
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [t(part)]},
                }
            )
    return blocks or [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": " "}}]},
        }
    ]


def md_title(md: str, fallback: str) -> str:
    for ln in md.splitlines():
        if ln.startswith("# "):
            return ln[2:].strip()
    return fallback
