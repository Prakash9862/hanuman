from pathlib import Path
from typing import cast

import pytest

from hanuman.models.chess_insight import (
    CHESS_INSIGHT_SCHEMA_VERSION,
    ChessInsight,
    ChessInsightEnvelope,
    ChessInsightEnvelopeError,
    InsightCategory,
    UnsupportedChessInsightSchemaError,
)
from hanuman.services.chess_insight_storage_service import (
    INSIGHTS_END,
    INSIGHTS_START,
    ChessInsightBlockError,
    inject_insight_block,
    parse_chess_note_insight_metadata,
    parse_insight_block,
    read_note_insights,
    render_insight_block,
)


def _insight(
    insight_id: str = "g1:1:blunder:player",
    *,
    category: InsightCategory = "blunder",
) -> ChessInsight:
    return ChessInsight(
        insight_id=insight_id,
        game_id="g1",
        category=category,
        subtype="opening",
        ply=1,
        move_number=1,
        color="white",
        san="Échec+",
        annotation=None,
        fen_before=None,
        fen_after=None,
        eval_before_cp=120,
        eval_after_cp=-100,
        loss_cp=220,
        best_move_san=None,
        principal_variation=("É4", "é5"),
        opening_phase=True,
        eco="B18",
        player_role="player",
    )


def _envelope(*insights: ChessInsight) -> ChessInsightEnvelope:
    return ChessInsightEnvelope(
        schema_version=CHESS_INSIGHT_SCHEMA_VERSION,
        game_id="g1",
        eco="B18",
        insights=tuple(insights),
    )


def test_empty_envelope_round_trip_is_deterministic_utf8() -> None:
    envelope = ChessInsightEnvelope(
        schema_version=1,
        game_id=None,
        eco="ÉCO",
        insights=(),
    )

    first = envelope.to_json()
    restored = ChessInsightEnvelope.from_json(first)

    assert restored == envelope
    assert restored.to_json() == first
    assert "ÉCO" in first
    assert "\\u00c9" not in first
    assert first.index('"eco"') < first.index('"game_id"') < first.index('"insights"')


def test_multiple_insights_round_trip_restores_tuples_and_none() -> None:
    envelope = _envelope(
        _insight(),
        _insight("g1:2:excellent:opponent", category="excellent"),
    )

    restored = ChessInsightEnvelope.from_json(envelope.to_json())

    assert restored == envelope
    assert isinstance(restored.insights, tuple)
    assert restored.insights[0].principal_variation == ("É4", "é5")
    assert restored.insights[0].annotation is None
    assert restored.insights[0].fen_before is None


def test_unknown_schema_version_is_rejected() -> None:
    with pytest.raises(UnsupportedChessInsightSchemaError, match="99"):
        ChessInsightEnvelope.from_json(
            '{"schema_version": 99, "game_id": null, "eco": null, "insights": []}'
        )


@pytest.mark.parametrize(
    "raw_json",
    [
        "{invalid",
        "[]",
        '{"schema_version": "1", "game_id": null, "eco": null, "insights": []}',
        '{"schema_version": 1, "game_id": 4, "eco": null, "insights": []}',
        '{"schema_version": 1, "game_id": null, "eco": null, "insights": {}}',
        '{"schema_version": 1, "game_id": null, "eco": null, "insights": [{}]}',
    ],
)
def test_invalid_json_or_structure_is_rejected(raw_json: str) -> None:
    with pytest.raises(ChessInsightEnvelopeError):
        ChessInsightEnvelope.from_json(raw_json)


def test_render_and_parse_insight_block() -> None:
    envelope = _envelope(_insight())

    rendered = render_insight_block(envelope)

    assert rendered.startswith(f"{INSIGHTS_START}\n```json\n")
    assert rendered.endswith(f"\n```\n{INSIGHTS_END}")
    assert parse_insight_block(rendered) == envelope


def test_injection_adds_once_replaces_and_is_idempotent() -> None:
    original = "# Partie\n\nContenu humain.\n"
    first_envelope = _envelope()
    second_envelope = _envelope(_insight())

    first = inject_insight_block(original, first_envelope)
    identical = inject_insight_block(first, first_envelope)
    replaced = inject_insight_block(first, second_envelope)

    assert identical == first
    assert replaced.count(INSIGHTS_START) == 1
    assert replaced.count(INSIGHTS_END) == 1
    assert parse_insight_block(replaced) == second_envelope
    assert replaced.startswith(original)


@pytest.mark.parametrize(
    "markdown",
    [
        f"# Partie\n{INSIGHTS_START}\n```json\n{{}}\n```",
        f"# Partie\n{INSIGHTS_END}",
        f"{INSIGHTS_START}\n{INSIGHTS_END}\n{INSIGHTS_START}\n{INSIGHTS_END}",
        f"{INSIGHTS_END}\n{INSIGHTS_START}",
        f"{INSIGHTS_START}\n{{}}\n{INSIGHTS_END}",
    ],
)
def test_incomplete_or_invalid_block_raises_business_error(markdown: str) -> None:
    with pytest.raises(ChessInsightBlockError):
        parse_insight_block(markdown)


def test_json_fence_outside_markers_is_ignored() -> None:
    markdown = """# Notes humaines

```json
{"schema_version": 99, "insights": "humain"}
```
"""

    assert parse_insight_block(markdown) is None


def test_injection_preserves_frontmatter_pgn_analysis_and_personal_notes() -> None:
    original = """---
game_id: "g1"
eco: B18
color: white
---

```pgn
1. e4 e5
```

<!-- HANUMAN_CHESS_ANALYSIS_START -->
## Analyse Stockfish visible
<!-- HANUMAN_CHESS_ANALYSIS_END -->

## Notes personnelles

- Garder [[ce lien]] et les accents.
"""

    updated = inject_insight_block(original, _envelope(_insight()))

    assert updated[: len(original)] == original
    assert original in updated


def test_read_note_and_parse_strict_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "partie.md"
    envelope = _envelope(_insight())
    markdown = '---\ngame_id: "g:é"\neco: B18\ncolor: black\n---\n\n# Partie\n'
    path.write_text(inject_insight_block(markdown, envelope), encoding="utf-8")

    assert read_note_insights(path) == envelope
    assert parse_chess_note_insight_metadata(markdown).game_id == "g:é"
    assert parse_chess_note_insight_metadata(markdown).eco == "B18"
    assert parse_chess_note_insight_metadata(markdown).player_color == "black"
    legacy = parse_chess_note_insight_metadata("# Ancienne note")
    assert legacy.game_id is None
    assert legacy.eco is None
    assert legacy.player_color is None


def test_frontmatter_rejects_invalid_color() -> None:
    markdown = "---\ngame_id: g1\neco: B18\ncolor: red\n---\n"

    with pytest.raises(ChessInsightBlockError, match="Couleur"):
        parse_chess_note_insight_metadata(markdown)


def test_injection_does_not_silently_overwrite_invalid_json_zone() -> None:
    markdown = f"{INSIGHTS_START}\n```json\n{{invalid\n```\n{INSIGHTS_END}"

    with pytest.raises(ChessInsightEnvelopeError):
        inject_insight_block(markdown, _envelope())


def test_model_rejects_invalid_category_during_deserialization() -> None:
    payload = _insight().to_dict()
    payload["category"] = "fork"

    with pytest.raises(ChessInsightEnvelopeError, match="Catégorie"):
        ChessInsight.from_dict(cast(dict[str, object], payload))
