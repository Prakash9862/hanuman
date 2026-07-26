import datetime as dt
from pathlib import Path

import pytest

from hanuman.models.chess import ChessGame, chess_game_path
from hanuman.models.chess_insight import ChessInsight, ChessInsightEnvelope
from hanuman.services.chess_insight_aggregation_service import (
    STATUS_CONFIRMED,
    STATUS_DURABLE,
    STATUS_EMERGING,
    aggregate_persisted_chess_insights,
    insight_status,
)
from hanuman.services.chess_insight_storage_service import (
    INSIGHTS_END,
    INSIGHTS_START,
    inject_insight_block,
)


def _game(index: int) -> ChessGame:
    return ChessGame(
        game_id=f"g{index}",
        end_time=dt.datetime(2024, 1, index, 12, tzinfo=dt.timezone.utc),
        white="prakasch",
        black=f"Opponent{index}",
        result="win",
        color="white",
        opening_name="Sicilian Defense",
        eco="B20",
        time_control="blitz",
        url=f"https://chess.com/game/{index}",
        pgn="1. e4 c5",
    )


def _insight(
    insight_id: str,
    game_id: str,
    *,
    category: str = "blunder",
    subtype: str = "opening",
    ply: int = 1,
) -> ChessInsight:
    return ChessInsight(
        insight_id=insight_id,
        game_id=game_id,
        category=category,  # type: ignore[arg-type]
        subtype=subtype,
        ply=ply,
        move_number=(ply + 1) // 2,
        color="white",
        san=f"Move{ply}",
        annotation="??",
        fen_before=None,
        fen_after=None,
        eval_before_cp=100,
        eval_after_cp=-100,
        loss_cp=200,
        best_move_san="e4",
        principal_variation=("e4", "e5"),
        opening_phase=subtype == "opening",
        eco="B20",
        player_role="player",
    )


def _write_note(
    root: Path,
    game: ChessGame,
    insights: tuple[ChessInsight, ...],
) -> None:
    path = chess_game_path(root, game)
    path.parent.mkdir(parents=True, exist_ok=True)
    envelope = ChessInsightEnvelope(1, game.game_id, game.eco, insights)
    path.write_text(
        inject_insight_block("# Partie\n", envelope),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (0, None),
        (2, None),
        (3, STATUS_EMERGING),
        (4, STATUS_CONFIRMED),
        (5, STATUS_DURABLE),
        (8, STATUS_DURABLE),
    ],
)
def test_thresholds_use_official_adr_statuses(
    count: int,
    expected: str | None,
) -> None:
    assert insight_status(count) == expected


def test_aggregation_groups_deduplicates_and_counts_unique_games(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Echecs"
    games = [_game(index) for index in range(1, 6)]
    for game in games:
        insights = (
            _insight(f"{game.game_id}:a", game.game_id),
            _insight(f"{game.game_id}:b", game.game_id, ply=3),
        )
        if game.game_id == "g1":
            insights += (insights[0],)
        _write_note(root, game, insights)

    result = aggregate_persisted_chess_insights(root, games)
    group = result.groups[0]

    assert (group.category, group.subtype) == ("blunder", "opening")
    assert group.unique_game_count == 5
    assert group.occurrence_count == 10
    assert group.status == STATUS_DURABLE
    assert result.diagnostics.duplicates_ignored == 1
    assert [item.game_date for item in group.occurrences[:2]] == [
        "2024-01-05",
        "2024-01-05",
    ]
    assert [item.insight.ply for item in group.occurrences[:2]] == [1, 3]
    assert group.occurrences[0].note_link.startswith("[[Echecs/2024/01/")
    assert group.occurrences[0].opponent == "Opponent5"


def test_many_occurrences_in_one_game_do_not_cross_threshold(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Echecs"
    game = _game(1)
    _write_note(
        root,
        game,
        tuple(_insight(f"g1:{index}", "g1", ply=index) for index in range(1, 7)),
    )

    group = aggregate_persisted_chess_insights(root, [game]).groups[0]

    assert group.occurrence_count == 6
    assert group.unique_game_count == 1
    assert group.status is None


def test_aggregation_reports_absent_invalid_unknown_and_unsupported(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Echecs"
    valid, absent, invalid, unknown = [_game(index) for index in range(1, 5)]
    _write_note(
        root,
        valid,
        (
            _insight(
                "motif",
                valid.game_id,
                category="motif",
                subtype="unimplemented",
            ),
        ),
    )
    invalid_path = chess_game_path(root, invalid)
    invalid_path.parent.mkdir(parents=True, exist_ok=True)
    invalid_path.write_text(
        f"{INSIGHTS_START}\n```json\n{{invalid\n```\n{INSIGHTS_END}",
        encoding="utf-8",
    )
    unknown_path = chess_game_path(root, unknown)
    unknown_path.write_text(
        f"""{INSIGHTS_START}
```json
{{"schema_version": 2, "game_id": "g4", "eco": "B20", "insights": []}}
```
{INSIGHTS_END}""",
        encoding="utf-8",
    )

    result = aggregate_persisted_chess_insights(root, [valid, absent, invalid, unknown])

    assert result.groups == ()
    assert result.diagnostics.blocks_valid == 1
    assert result.diagnostics.blocks_absent == 1
    assert result.diagnostics.blocks_invalid == 1
    assert result.diagnostics.versions_unknown == 1
    assert result.diagnostics.unsupported_insights_ignored == 1


def test_aggregation_is_stable_when_game_input_order_changes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Echecs"
    games = [_game(index) for index in range(1, 4)]
    for game in games:
        _write_note(
            root,
            game,
            (_insight(f"{game.game_id}:1", game.game_id),),
        )

    first = aggregate_persisted_chess_insights(root, games)
    second = aggregate_persisted_chess_insights(root, list(reversed(games)))

    assert second == first
