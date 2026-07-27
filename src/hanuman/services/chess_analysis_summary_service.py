from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from hanuman.models.chess import ChessGame, chess_game_path
from hanuman.services.delimited_zone_service import (
    DelimitedZoneError,
    find_delimited_zone,
)

ANALYSIS_START = "<!-- HANUMAN_CHESS_ANALYSIS_START -->"
ANALYSIS_END = "<!-- HANUMAN_CHESS_ANALYSIS_END -->"
AnalysisStatus = Literal["analysed", "pending", "unreadable"]


@dataclass(frozen=True)
class ChessAnalysisSummary:
    status: AnalysisStatus
    engine: str | None = None
    depth: int | None = None
    average_loss_cp: float | None = None
    blunders: int = 0
    mistakes: int = 0
    dubious: int = 0
    excellent: int = 0
    missed_excellent: int = 0
    worst_move: str | None = None
    turning_point: str | None = None

    @property
    def analysed(self) -> bool:
        return self.status == "analysed"


@dataclass(frozen=True)
class ChessProfileStats:
    games_total: int
    games_analysed: int
    games_pending: int
    games_unreadable: int
    total_blunders: int
    total_mistakes: int
    total_dubious: int
    total_excellent: int
    total_missed_excellent: int
    average_blunders_per_analysed_game: float
    average_mistakes_per_analysed_game: float
    average_dubious_per_analysed_game: float
    average_excellent_per_analysed_game: float
    average_missed_excellent_per_analysed_game: float
    average_loss_cp: float | None
    analysis_coverage_percent: float


FIELD_PATTERNS = {
    "engine": re.compile(r"^\s*-\s*\*\*Moteur\s*:\*\*\s*(.*?)\s*$", re.MULTILINE),
    "depth": re.compile(r"^\s*-\s*\*\*Profondeur\s*:\*\*\s*(\d+)\s*$", re.MULTILINE),
    "average_loss_cp": re.compile(
        r"^\s*-\s*\*\*Perte moyenne\s*:\*\*\s*(\d+(?:[.,]\d+)?)\s*cp\b.*$",
        re.MULTILINE,
    ),
    "worst_move": re.compile(r"^\s*-\s*\*\*Pire coup\s*:\*\*\s*(.*?)\s*$", re.MULTILINE),
    "turning_point": re.compile(
        r"^\s*-\s*\*\*Moment de bascule\s*:\*\*\s*(.*?)\s*$",
        re.MULTILINE,
    ),
}
COUNT_PATTERNS = {
    "blunders": re.compile(r"^\s*\|\s*`?\?\?`?\s+Gaffes\s*\|\s*(\d+)\s*\|\s*$"),
    "mistakes": re.compile(r"^\s*\|\s*`?\?`?\s+Erreurs\s*\|\s*(\d+)\s*\|\s*$"),
    "dubious": re.compile(r"^\s*\|\s*`?\?!`?\s+Coups douteux\s*\|\s*(\d+)\s*\|\s*$"),
    "excellent": re.compile(r"^\s*\|\s*`?!!`?\s+Excellents coups\s*\|\s*(\d+)\s*\|\s*$"),
    "missed_excellent": re.compile(r"^\s*\|\s*Excellents coups manqués\s*\|\s*(\d+)\s*\|\s*$"),
}


def _analysis_block(markdown: str) -> tuple[str | None, bool]:
    try:
        bounds = find_delimited_zone(
            markdown,
            ANALYSIS_START,
            ANALYSIS_END,
            label="d’analyse Chess",
        )
    except DelimitedZoneError:
        return None, True
    if bounds is None:
        return None, False
    return (
        markdown[bounds.start + len(ANALYSIS_START) : bounds.end - len(ANALYSIS_END)],
        False,
    )


def _optional_text(block: str, field: str) -> str | None:
    match = FIELD_PATTERNS[field].search(block)
    if not match:
        return None
    value = match.group(1).strip()
    return None if value in {"", "—"} else value


def parse_analysis_summary(markdown: str) -> ChessAnalysisSummary:
    """Relit uniquement le bloc d'analyse Hanuman déjà présent dans une note."""

    block, malformed_markers = _analysis_block(markdown)
    if malformed_markers:
        return ChessAnalysisSummary(status="unreadable")
    if block is None or "Analyse non encore lancée." in block:
        return ChessAnalysisSummary(status="pending")
    if "### Ton bilan" not in block:
        return ChessAnalysisSummary(status="unreadable")

    counts: dict[str, int] = {}
    for line in block.splitlines():
        for name, pattern in COUNT_PATTERNS.items():
            match = pattern.match(line)
            if match:
                counts[name] = int(match.group(1))
    if set(counts) != set(COUNT_PATTERNS):
        return ChessAnalysisSummary(status="unreadable")

    depth_text = _optional_text(block, "depth")
    loss_text = _optional_text(block, "average_loss_cp")
    try:
        depth = int(depth_text) if depth_text is not None else None
        average_loss = float(loss_text.replace(",", ".")) if loss_text is not None else None
    except ValueError:
        return ChessAnalysisSummary(status="unreadable")

    return ChessAnalysisSummary(
        status="analysed",
        engine=_optional_text(block, "engine"),
        depth=depth,
        average_loss_cp=average_loss,
        blunders=counts["blunders"],
        mistakes=counts["mistakes"],
        dubious=counts["dubious"],
        excellent=counts["excellent"],
        missed_excellent=counts["missed_excellent"],
        worst_move=_optional_text(block, "worst_move"),
        turning_point=_optional_text(block, "turning_point"),
    )


def read_analysis_summary(path: Path) -> ChessAnalysisSummary:
    if not path.is_file():
        return ChessAnalysisSummary(status="pending")
    try:
        return parse_analysis_summary(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return ChessAnalysisSummary(status="unreadable")


def _rounded_average(total: int, count: int) -> float:
    return round(total / count, 2) if count else 0.0


def aggregate_analysis_summaries(
    games_total: int,
    summaries: list[ChessAnalysisSummary],
) -> ChessProfileStats:
    analysed = [summary for summary in summaries if summary.analysed]
    analysed_count = len(analysed)
    pending_count = sum(summary.status == "pending" for summary in summaries)
    unreadable_count = sum(summary.status == "unreadable" for summary in summaries)
    total_blunders = sum(summary.blunders for summary in analysed)
    total_mistakes = sum(summary.mistakes for summary in analysed)
    total_dubious = sum(summary.dubious for summary in analysed)
    total_excellent = sum(summary.excellent for summary in analysed)
    total_missed = sum(summary.missed_excellent for summary in analysed)
    losses = [
        summary.average_loss_cp for summary in analysed if summary.average_loss_cp is not None
    ]
    return ChessProfileStats(
        games_total=games_total,
        games_analysed=analysed_count,
        games_pending=pending_count,
        games_unreadable=unreadable_count,
        total_blunders=total_blunders,
        total_mistakes=total_mistakes,
        total_dubious=total_dubious,
        total_excellent=total_excellent,
        total_missed_excellent=total_missed,
        average_blunders_per_analysed_game=_rounded_average(total_blunders, analysed_count),
        average_mistakes_per_analysed_game=_rounded_average(total_mistakes, analysed_count),
        average_dubious_per_analysed_game=_rounded_average(total_dubious, analysed_count),
        average_excellent_per_analysed_game=_rounded_average(total_excellent, analysed_count),
        average_missed_excellent_per_analysed_game=_rounded_average(total_missed, analysed_count),
        average_loss_cp=round(sum(losses) / len(losses), 1) if losses else None,
        analysis_coverage_percent=(
            round(analysed_count / games_total * 100, 1) if games_total else 0.0
        ),
    )


def build_chess_profile_stats(root: Path, games: list[ChessGame]) -> ChessProfileStats:
    summaries = [read_analysis_summary(chess_game_path(root, game)) for game in games]
    return aggregate_analysis_summaries(len(games), summaries)
