from __future__ import annotations

from typing import Any, Dict, List

from hanuman.services.core.obsidian_service import md_title, md_to_blocks


def _collect(blocks: List[Dict[str, Any]], btype: str) -> List[Dict[str, Any]]:
    return [b for b in blocks if b.get("type") == btype]


def test_md_to_blocks_parses_headings_lists_and_paragraphs() -> None:
    md = """# Big Title

## Section 1
Un premier paragraphe.

- Item 1
- Item 2

1. Premier
2. Deuxième
"""

    blocks = md_to_blocks(md)

    # Le H1 est ignoré (sert de titre ailleurs), mais le H2 est bien présent
    headings2 = _collect(blocks, "heading_2")
    assert any(h["heading_2"]["rich_text"][0]["text"]["content"] == "Section 1" for h in headings2)

    # Les items à puces
    bullets = _collect(blocks, "bulleted_list_item")
    bullet_texts = [b["bulleted_list_item"]["rich_text"][0]["text"]["content"] for b in bullets]
    assert bullet_texts == ["Item 1", "Item 2"]

    # Les listes numérotées
    ordered = _collect(blocks, "numbered_list_item")
    ordered_texts = [b["numbered_list_item"]["rich_text"][0]["text"]["content"] for b in ordered]
    assert ordered_texts == ["Premier", "Deuxième"]

    # Un paragraphe simple doit exister (avec du texte)
    paragraphs = _collect(blocks, "paragraph")
    non_empty_paragraphs = [p for p in paragraphs if p["paragraph"].get("rich_text")]

    assert any(
        "premier paragraphe" in p["paragraph"]["rich_text"][0]["text"]["content"].lower()
        for p in non_empty_paragraphs
    )


def test_md_to_blocks_long_line_is_chunked() -> None:
    long_text = "x" * 4000
    md = long_text  # une seule ligne très longue

    blocks = md_to_blocks(md)
    paragraphs = _collect(blocks, "paragraph")

    # Chaque chunk donne un paragraphe, donc ≥ 2
    assert len(paragraphs) >= 2

    total_len = sum(len(p["paragraph"]["rich_text"][0]["text"]["content"]) for p in paragraphs)
    assert total_len == len(long_text)


def test_md_title_prefers_h1_and_falls_back_to_filename() -> None:
    md = """# Mon Titre

Du texte ensuite.
"""
    assert md_title(md, fallback="Fallback") == "Mon Titre"

    md2 = "Pas de titre ici"
    assert md_title(md2, fallback="Fallback-2") == "Fallback-2"
