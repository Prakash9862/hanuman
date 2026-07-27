from __future__ import annotations

import pytest

from hanuman.services.chess_generated_frontmatter_service import (
    CHESS_MANAGED_TAG_PREFIXES,
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


def test_merges_block_tags_preserving_human_order_and_replacing_chess_tags() -> None:
    existing = (
        "---\n"
        "tags:\n"
        "  - premier-humain\n"
        "  - chess/analysis/pending\n"
        "  - échec-humain\n"
        "  - premier-humain\n"
        "  - chess/obsolete\n"
        "---\n"
    )
    generated = (
        "---\n"
        "tags:\n"
        "  - chess/game\n"
        "  - chess/analysis/analysed\n"
        "  - chess/game\n"
        "---\n"
    )

    updated = update_generated_frontmatter(
        existing,
        generated,
        owned_keys=frozenset({"tags"}),
        label="de test",
        managed_tag_prefixes=CHESS_MANAGED_TAG_PREFIXES,
    )

    assert updated == (
        "---\n"
        "tags:\n"
        "  - premier-humain\n"
        "  - échec-humain\n"
        "  - chess/game\n"
        "  - chess/analysis/analysed\n"
        "---\n"
    )
    assert (
        update_generated_frontmatter(
            updated,
            generated,
            owned_keys=frozenset({"tags"}),
            label="de test",
            managed_tag_prefixes=CHESS_MANAGED_TAG_PREFIXES,
        )
        == updated
    )


def test_merges_supported_flow_tags_without_losing_quotes() -> None:
    existing = "---\ntags: [chess/dashboard, 'humain-un', \"échec-humain\"]\n---\n"
    generated = "---\ntags:\n  - chess/profile\n---\n"

    updated = update_generated_frontmatter(
        existing,
        generated,
        owned_keys=frozenset({"tags"}),
        label="de test",
        managed_tag_prefixes=CHESS_MANAGED_TAG_PREFIXES,
    )

    assert updated == "---\ntags: ['humain-un', \"échec-humain\", chess/profile]\n---\n"


@pytest.mark.parametrize(
    "tags",
    [
        "tags:\n  valeur-inattendue\n",
        "tags:\n  - humain # commentaire\n",
        "tags: [humain,]\n",
        "tags: {humain: oui}\n",
    ],
)
def test_refuses_unsupported_tags_without_changing_source(tags: str) -> None:
    existing = f"---\n{tags}human: intact\n---\n"

    with pytest.raises(ChessGeneratedFrontmatterError):
        update_generated_frontmatter(
            existing,
            "---\ntags:\n  - chess/dashboard\n---\n",
            owned_keys=frozenset({"tags"}),
            label="de test",
            managed_tag_prefixes=CHESS_MANAGED_TAG_PREFIXES,
        )

    assert "human: intact" in existing
