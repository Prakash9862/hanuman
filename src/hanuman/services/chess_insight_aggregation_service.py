from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from hanuman.models.chess import ChessGame, chess_game_note_link, chess_game_path
from hanuman.models.chess_insight import (
    ChessInsight,
    InsightCategory,
    UnsupportedChessInsightSchemaError,
)
from hanuman.services.chess_insight_storage_service import (
    ChessInsightBlockError,
    parse_insight_block,
)

INSIGHT_THRESHOLD_EMERGING = 3
INSIGHT_THRESHOLD_CONFIRMED = 4
INSIGHT_THRESHOLD_DURABLE = 5

InsightStatus = Literal[
    "Signal émergent",
    "Tendance confirmée",
    "Synthèse durable",
]
STATUS_EMERGING: Final[InsightStatus] = "Signal émergent"
STATUS_CONFIRMED: Final[InsightStatus] = "Tendance confirmée"
STATUS_DURABLE: Final[InsightStatus] = "Synthèse durable"
STATUS_INACTIVE: Final = "Inactive — seuil actuellement non atteint"

SUPPORTED_GROUPS: tuple[tuple[InsightCategory, str], ...] = (
    ("blunder", "opening"),
    ("blunder", "middlegame_or_endgame"),
    ("excellent", "opening"),
    ("excellent", "middlegame_or_endgame"),
    ("opportunity", "missed_excellent"),
)


@dataclass(frozen=True)
class ChessInsightOccurrence:
    insight: ChessInsight
    game_id: str
    note_path: Path
    note_link: str
    game_date: str | None
    opponent: str | None
    result: str | None
    color: str | None


@dataclass(frozen=True)
class ChessInsightGroup:
    category: InsightCategory
    subtype: str
    occurrences: tuple[ChessInsightOccurrence, ...]
    occurrence_count: int
    unique_game_count: int
    status: InsightStatus | None


@dataclass(frozen=True)
class ChessInsightDiagnostics:
    notes_total: int
    blocks_valid: int
    blocks_absent: int
    blocks_invalid: int
    versions_unknown: int
    duplicates_ignored: int
    unsupported_insights_ignored: int


@dataclass(frozen=True)
class ChessInsightAggregation:
    groups: tuple[ChessInsightGroup, ...]
    diagnostics: ChessInsightDiagnostics


def insight_status(unique_game_count: int) -> InsightStatus | None:
    if unique_game_count >= INSIGHT_THRESHOLD_DURABLE:
        return STATUS_DURABLE
    if unique_game_count >= INSIGHT_THRESHOLD_CONFIRMED:
        return STATUS_CONFIRMED
    if unique_game_count >= INSIGHT_THRESHOLD_EMERGING:
        return STATUS_EMERGING
    return None


def _ordered_occurrences(
    occurrences: list[ChessInsightOccurrence],
) -> tuple[ChessInsightOccurrence, ...]:
    ordered = sorted(
        occurrences,
        key=lambda item: (
            str(item.note_path),
            item.insight.ply,
            item.insight.insight_id,
        ),
    )
    ordered.sort(key=lambda item: item.game_date or "", reverse=True)
    return tuple(ordered)


def aggregate_persisted_chess_insights(
    root: Path,
    games: list[ChessGame],
) -> ChessInsightAggregation:
    candidates: list[ChessInsightOccurrence] = []
    blocks_valid = 0
    blocks_absent = 0
    blocks_invalid = 0
    versions_unknown = 0

    for game in sorted(games, key=lambda item: (item.end_time, item.game_id)):
        path = chess_game_path(root, game)
        if not path.is_file():
            blocks_absent += 1
            continue
        try:
            envelope = parse_insight_block(path.read_text(encoding="utf-8"))
        except UnsupportedChessInsightSchemaError:
            versions_unknown += 1
            continue
        except (ChessInsightBlockError, ValueError, OSError, UnicodeError):
            blocks_invalid += 1
            continue
        if envelope is None:
            blocks_absent += 1
            continue
        blocks_valid += 1
        for insight in envelope.insights:
            candidates.append(
                ChessInsightOccurrence(
                    insight=insight,
                    game_id=game.game_id,
                    note_path=path,
                    note_link=chess_game_note_link(game),
                    game_date=game.end_time.strftime("%Y-%m-%d"),
                    opponent=game.opponent,
                    result=game.result,
                    color=game.color,
                )
            )

    candidates.sort(
        key=lambda item: (
            item.insight.insight_id,
            str(item.note_path),
            item.insight.category,
            item.insight.subtype or "",
        )
    )
    deduplicated: list[ChessInsightOccurrence] = []
    seen_ids: set[str] = set()
    duplicates_ignored = 0
    for occurrence in candidates:
        if occurrence.insight.insight_id in seen_ids:
            duplicates_ignored += 1
            continue
        seen_ids.add(occurrence.insight.insight_id)
        deduplicated.append(occurrence)

    grouped: dict[tuple[InsightCategory, str], list[ChessInsightOccurrence]] = {}
    unsupported = 0
    supported = set(SUPPORTED_GROUPS)
    for occurrence in deduplicated:
        key = (occurrence.insight.category, occurrence.insight.subtype or "")
        if key not in supported:
            unsupported += 1
            continue
        grouped.setdefault(key, []).append(occurrence)

    groups: list[ChessInsightGroup] = []
    for category, subtype in SUPPORTED_GROUPS:
        occurrences = grouped.get((category, subtype))
        if not occurrences:
            continue
        ordered = _ordered_occurrences(occurrences)
        unique_games = len({occurrence.game_id for occurrence in ordered})
        groups.append(
            ChessInsightGroup(
                category=category,
                subtype=subtype,
                occurrences=ordered,
                occurrence_count=len(ordered),
                unique_game_count=unique_games,
                status=insight_status(unique_games),
            )
        )

    return ChessInsightAggregation(
        groups=tuple(groups),
        diagnostics=ChessInsightDiagnostics(
            notes_total=len(games),
            blocks_valid=blocks_valid,
            blocks_absent=blocks_absent,
            blocks_invalid=blocks_invalid,
            versions_unknown=versions_unknown,
            duplicates_ignored=duplicates_ignored,
            unsupported_insights_ignored=unsupported,
        ),
    )
