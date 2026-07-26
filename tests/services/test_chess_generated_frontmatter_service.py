from __future__ import annotations

import pytest

from hanuman.services.chess_generated_frontmatter_service import (
    ChessGeneratedFrontmatterError,
    update_generated_frontmatter,
)


def test_updates_owned_keys_and_preserves_human_content() -> None:
    existing = (
        "---\n"
        "type: chess-dashboard\n"
        "games_count: 2\n"
        "human_key: \"Valeur Échec\"\n"
        "# commentaire humain\n"
        "---\n"
        "\n"
        "Corps humain\n"
    )
    generated = "---\ntype: chess-dashboard\ngames_count: 8\n---\n"

    updated = update_generated_frontmatter(
        existing,
        generated,
        owned_keys=frozenset({"type", "games_count"}),
        label="de test",
    )

    assert "games_count: 8\n" in updated
    assert 'human_key: "Valeur Échec"\n# commentaire humain\n' in updated
    assert updated.endswith("\nCorps humain\n")


def test_preserves_crlf_for_generated_fields() -> None:
    existing = "---\r\ntype: chess-dashboard\r\ngames_count: 2\r\nhuman: oui\r\n---\r\nBody\r\n"
    generated = "---\ntype: chess-dashboard\ngames_count: 8\n---\n"

    updated = update_generated_frontmatter(
        existing,
        generated,
        owned_keys=frozenset({"type", "games_count"}),
        label="de test",
    )

    assert updated == (
        "---\r\ntype: chess-dashboard\r\ngames_count: 8\r\n" "human: oui\r\n---\r\nBody\r\n"
    )


@pytest.mark.parametrize(
    "existing",
    [
        "sans frontmatter",
        "---\ntype: chess-dashboard\n",
        "---\ntype: chess-dashboard\ntype: autre\n---\n",
        "---\ntype: chess-dashboard # humain\n---\n",
    ],
)
def test_refuses_ambiguous_frontmatter(existing: str) -> None:
    with pytest.raises(ChessGeneratedFrontmatterError):
        update_generated_frontmatter(
            existing,
            "---\ntype: chess-dashboard\n---\n",
            owned_keys=frozenset({"type"}),
            label="de test",
        )
