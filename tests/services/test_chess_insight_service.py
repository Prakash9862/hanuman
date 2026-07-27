from dataclasses import replace
from typing import cast

import pytest

from hanuman.models.chess_insight import ChessInsight, InsightCategory
from hanuman.services.chess_analysis_service import GameAnalysis, MoveAnalysis
from hanuman.services.chess_insight_service import build_chess_insights


def _move(
    ply: int,
    *,
    color: str = "white",
    classification: str = "normal",
    excellent: bool = False,
    missed_excellent: bool = False,
    opening_phase: bool = True,
) -> MoveAnalysis:
    return MoveAnalysis(
        ply=ply,
        move_number=(ply + 1) // 2,
        color=color,
        san=f"Move{ply}",
        uci="e2e4",
        eval_before_cp=120,
        eval_after_cp=-100,
        loss_cp=220,
        annotation="??" if classification == "blunder" else "",
        classification=classification,
        best_move_san="e4",
        best_move_uci="e2e4",
        principal_variation=["e4", "e5", "Nf3"],
        turning_point=False,
        excellent=excellent,
        missed_excellent=missed_excellent,
        opening_phase=opening_phase,
    )


def _analysis(moves: list[MoveAnalysis]) -> GameAnalysis:
    return GameAnalysis(
        white="prakasch",
        black="Opponent",
        result="1-0",
        eco="B20",
        opening="Sicilian Defense",
        engine="Fixture",
        depth=18,
        moves=moves,
        counts={},
        average_centipawn_loss=0.0,
        worst_move=None,
        turning_point_ply=None,
    )


def _minimal_insight(**changes: object) -> ChessInsight:
    values: dict[str, object] = {
        "insight_id": "g1:1:blunder:player",
        "game_id": "g1",
        "category": "blunder",
        "subtype": "opening",
        "ply": 1,
        "move_number": 1,
        "color": "white",
        "san": "e4",
        "annotation": None,
        "fen_before": None,
        "fen_after": None,
        "eval_before_cp": 100,
        "eval_after_cp": -100,
        "loss_cp": 200,
        "best_move_san": None,
        "principal_variation": (),
        "opening_phase": True,
        "eco": None,
        "player_role": "player",
    }
    values.update(changes)
    return ChessInsight(**values)  # type: ignore[arg-type]


def test_chess_insight_serialization_is_stable_and_json_compatible() -> None:
    insight = _minimal_insight(
        principal_variation=("e4", "e5"),
        annotation=None,
        fen_before=None,
        fen_after=None,
    )

    assert insight.to_dict() == {
        "insight_id": "g1:1:blunder:player",
        "game_id": "g1",
        "category": "blunder",
        "subtype": "opening",
        "ply": 1,
        "move_number": 1,
        "color": "white",
        "san": "e4",
        "annotation": None,
        "fen_before": None,
        "fen_after": None,
        "eval_before_cp": 100,
        "eval_after_cp": -100,
        "loss_cp": 200,
        "best_move_san": None,
        "principal_variation": ["e4", "e5"],
        "opening_phase": True,
        "eco": None,
        "player_role": "player",
    }
    assert insight.to_dict() == insight.to_dict()


def test_chess_insight_rejects_category_outside_closed_set() -> None:
    with pytest.raises(ValueError, match="Catégorie"):
        _minimal_insight(category=cast(InsightCategory, "fork"))


def test_build_blunders_distinguishes_player_and_opponent() -> None:
    analysis = _analysis(
        [
            _move(1, classification="blunder"),
            _move(2, color="black", classification="blunder"),
        ]
    )

    insights = build_chess_insights(analysis, player_color="white", game_id="game-1")

    assert [(item.category, item.player_role) for item in insights] == [
        ("blunder", "player"),
        ("blunder", "opponent"),
    ]
    assert [item.insight_id for item in insights] == [
        "game-1:1:blunder:player",
        "game-1:2:blunder:opponent",
    ]


def test_build_excellent_emits_one_event_when_both_flags_match() -> None:
    analysis = _analysis([_move(1, classification="excellent", excellent=True)])

    insights = build_chess_insights(analysis, player_color="white")

    assert len(insights) == 1
    assert insights[0].category == "excellent"


def test_build_missed_excellent_can_coexist_with_blunder() -> None:
    analysis = _analysis([_move(1, classification="blunder", missed_excellent=True)])

    insights = build_chess_insights(analysis, player_color="white")

    assert [item.category for item in insights] == ["blunder", "opportunity"]
    assert insights[1].subtype == "missed_excellent"


@pytest.mark.parametrize("classification", ["mistake", "dubious", "normal"])
def test_build_ignores_other_classifications(classification: str) -> None:
    assert (
        build_chess_insights(
            _analysis([_move(1, classification=classification)]),
            player_color="white",
        )
        == ()
    )


def test_build_preserves_chronology_without_motifs_or_duplicates() -> None:
    repeated = _move(3, classification="excellent", excellent=True)
    analysis = _analysis(
        [
            repeated,
            _move(1, classification="blunder"),
            replace(repeated),
            _move(2, color="black", missed_excellent=True),
        ]
    )

    insights = build_chess_insights(analysis, player_color="white")

    assert [(item.ply, item.category) for item in insights] == [
        (1, "blunder"),
        (2, "opportunity"),
        (3, "excellent"),
    ]
    assert all(item.category != "motif" for item in insights)
    assert len({item.insight_id for item in insights}) == len(insights)


def test_build_propagates_game_eco_phase_and_optional_fen() -> None:
    analysis = _analysis(
        [
            _move(1, classification="blunder", opening_phase=True),
            _move(30, classification="blunder", opening_phase=False),
        ]
    )

    insights = build_chess_insights(
        analysis,
        player_color="white",
        game_id="g42",
        eco="C42",
    )

    assert [item.subtype for item in insights] == [
        "opening",
        "middlegame_or_endgame",
    ]
    assert all(item.game_id == "g42" and item.eco == "C42" for item in insights)
    assert all(item.fen_before is None and item.fen_after is None for item in insights)


def test_build_copies_principal_variation_without_mutation() -> None:
    move = _move(1, classification="blunder")
    analysis = _analysis([move])

    insight = build_chess_insights(analysis, player_color="white")[0]
    move.principal_variation.append("Nc6")

    assert insight.principal_variation == ("e4", "e5", "Nf3")


def test_build_is_deterministic_with_game_id_and_derived_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = _analysis([_move(1, classification="blunder")])

    first = build_chess_insights(analysis, player_color="white")
    monkeypatch.setenv("CHESS_COM_USERNAME", "unrelated-user")
    second = build_chess_insights(analysis, player_color="white")

    assert first == second
    assert first[0].insight_id.startswith("derived-")
    assert build_chess_insights(
        analysis, player_color="white", game_id="explicit"
    ) == build_chess_insights(analysis, player_color="white", game_id="explicit")
