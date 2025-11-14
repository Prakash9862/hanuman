from __future__ import annotations

import io
import textwrap
import urllib.error
from pathlib import Path
from typing import Any, Dict, List

from hanuman.orchestrations import obsidian_to_notion as o2n
from hanuman.orchestrations.obsidian_to_notion import FrontMatter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mk_markdown_file(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "note.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# split_frontmatter / FrontMatter
# ---------------------------------------------------------------------------


def test_split_frontmatter_with_yaml_frontmatter() -> None:
    md = textwrap.dedent(
        """\
        ---
        title: Mon titre
        summary: Petite description
        tags: [foo, bar]
        date: 2025-11-14
        extra: valeur-supplémentaire
        ---

        Contenu du fichier.
        Deuxième ligne.
        """
    )

    fm, body = o2n.split_frontmatter(md)

    assert isinstance(fm, FrontMatter)
    assert fm.title == "Mon titre"
    assert fm.summary == "Petite description"
    assert fm.tags == ["foo", "bar"]
    assert fm.date == "2025-11-14"
    assert fm.extra_props == {"extra": "valeur-supplémentaire"}
    assert "Contenu du fichier." in body
    assert "Deuxième ligne." in body


def test_split_frontmatter_without_frontmatter() -> None:
    md = textwrap.dedent(
        """\
        Titre simple

        Corps du texte sans frontmatter.
        """
    )

    fm, body = o2n.split_frontmatter(md)

    # Tout est vide par défaut
    assert fm.title is None
    assert fm.summary is None
    assert fm.tags == []
    assert fm.date is None
    assert fm.extra_props == {}
    # Le corps est intact
    assert "Corps du texte" in body


# ---------------------------------------------------------------------------
# md_to_blocks
# ---------------------------------------------------------------------------


def test_md_to_blocks_heading_and_paragraph() -> None:
    md = textwrap.dedent(
        """\
        # Titre principal

        Paragraphe de texte normal.
        """
    )

    blocks = o2n.md_to_blocks(md)

    assert len(blocks) == 2

    heading = blocks[0]
    assert heading["type"] == "heading_1"
    assert heading["heading_1"]["rich_text"][0]["text"]["content"] == "Titre principal"

    para = blocks[1]
    assert para["type"] == "paragraph"
    assert (
        para["paragraph"]["rich_text"][0]["text"]["content"]
        == "Paragraphe de texte normal."
    )


def test_md_to_blocks_list_and_code_block() -> None:
    md = textwrap.dedent(
        """\
        - item 1
        - item 2

        ```python
        print("hello")
        ```
        """
    )

    blocks = o2n.md_to_blocks(md)

    # On doit avoir une liste + un code block
    types = [b["type"] for b in blocks]
    assert "bulleted_list_item" in types
    assert "code" in types

    code_blocks = [b for b in blocks if b["type"] == "code"]
    assert len(code_blocks) == 1
    code = code_blocks[0]
    assert code["code"]["language"] == "python"
    assert code["code"]["rich_text"][0]["text"]["content"] == 'print("hello")'


# ---------------------------------------------------------------------------
# build_notion_body
# ---------------------------------------------------------------------------


def test_build_notion_body_for_database_parent() -> None:
    front = FrontMatter(
        title="Note depuis Obsidian",
        summary="Petit résumé",
        tags=["a", "b"],
        date="2025-11-14",
        extra_props={"extra": "x"},
    )
    body_md = "## Sous-titre\n\nUn peu de contenu."

    body = o2n.build_notion_body(
        markdown_path="notes/note.md",
        parent_id="db-123",
        parent_is_db=True,
        front=front,
        body_md=body_md,
    )

    assert body["parent"] == {"database_id": "db-123"}
    props = body["properties"]

    # Champs principaux bien mappés
    assert props["Name"]["title"][0]["text"]["content"] == "Note depuis Obsidian"
    assert props["Résumé"]["rich_text"][0]["text"]["content"] == "Petit résumé"
    assert {t["name"] for t in props["Tags"]["multi_select"]} == {"a", "b"}
    assert props["Date"]["date"]["start"] == "2025-11-14"
    assert props["extra"]["rich_text"][0]["text"]["content"] == "x"

    # On a bien un callout de métadonnées en premier enfant
    children: List[Dict[str, Any]] = body["children"]
    assert children[0]["type"] == "callout"
    callout_text = children[0]["callout"]["rich_text"][0]["text"]["content"]
    assert "Résumé:" in callout_text
    assert "Tags:" in callout_text


def test_build_notion_body_for_page_parent() -> None:
    front = FrontMatter(
        title="Titre en page enfant",
        summary=None,
        tags=[],
        date=None,
        extra_props={},
    )
    body_md = "Paragraphe **simple**."

    body = o2n.build_notion_body(
        markdown_path="note.md",
        parent_id="page-456",
        parent_is_db=False,
        front=front,
        body_md=body_md,
    )

    assert body["parent"] == {"page_id": "page-456"}
    children: List[Dict[str, Any]] = body["children"]

    # Premier block = heading avec le titre
    heading = children[0]
    assert heading["type"] == "heading_1"
    assert (
        heading["heading_1"]["rich_text"][0]["text"]["content"]
        == "Titre en page enfant"
    )

    # Le reste vient du markdown
    assert any(b["type"] == "paragraph" for b in children[1:])


# ---------------------------------------------------------------------------
# send_markdown_to_notion
# ---------------------------------------------------------------------------


def test_send_markdown_to_notion_success_path(tmp_path: Path, monkeypatch: Any) -> None:
    md = textwrap.dedent(
        """\
        ---
        title: Fichier pour Notion
        summary: Test en succès
        tags: [ok]
        ---

        Contenu minimal.
        """
    )
    md_path = _mk_markdown_file(tmp_path, md)

    captured_payload: Dict[str, Any] = {}

    def fake_post(body: Dict[str, Any]) -> Dict[str, Any]:
        captured_payload.update(body)
        return {"id": "fake-page-id", "body": body}

    monkeypatch.setattr(o2n, "_post_create_page", fake_post)

    result = o2n.send_markdown_to_notion(
        markdown_path=str(md_path),
        parent_id="db-coverage",
        parent_is_db=True,
        notion_token="test-token",
        notion_version="2025-09-03",
    )

    assert result["id"] == "fake-page-id"
    assert captured_payload["parent"]["database_id"] == "db-coverage"


def test_send_markdown_to_notion_fallback_page_parent_on_validation_error(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """On simule un validation_error Notion sur database_id,
    puis on vérifie le retry en page_id.
    """

    md = textwrap.dedent(
        """\
        ---
        title: Fichier avec fallback
        ---

        Corps.
        """
    )
    md_path = _mk_markdown_file(tmp_path, md)

    calls: List[Dict[str, Any]] = []

    def fake_post(body: Dict[str, Any]) -> Dict[str, Any]:
        # Première tentative : on lève une HTTPError avec "validation_error"
        calls.append(body)
        if len(calls) == 1:
            fp = io.BytesIO(b'{"object":"error","code":"validation_error"}')
            raise urllib.error.HTTPError(
                url="https://api.notion.com/v1/pages",
                code=400,
                msg="Bad Request",
                hdrs=None,
                fp=fp,
            )
        # Deuxième tentative : succès avec parent page_id
        return {"id": "ok-page", "parent": body["parent"]}

    monkeypatch.setattr(o2n, "_post_create_page", fake_post)

    result = o2n.send_markdown_to_notion(
        markdown_path=str(md_path),
        parent_id="parent-xyz",
        parent_is_db=True,
        notion_token="test-token",
        notion_version="2025-09-03",
    )

    # Deux appels : 1 fois avec database_id, 1 fois avec page_id
    assert len(calls) == 2
    assert "database_id" in calls[0]["parent"]
    assert "page_id" in calls[1]["parent"]
    assert result["id"] == "ok-page"
