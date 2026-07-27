from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import cast

from hanuman.models.chess_insight import ChessColor, ChessInsight, InsightCategory
from hanuman.services.chess_analysis_service import AnalysisConfig
from hanuman.services.chess_analysis_summary_service import (
    ANALYSIS_END,
    ANALYSIS_START,
    parse_analysis_summary,
)
from hanuman.services.delimited_zone_service import (
    DelimitedZoneError,
    find_delimited_zone,
)


class ChessAnalysisInsightError(ValueError):
    """Signale un bloc d'analyse inutilisable pour reconstruire les index."""


@dataclass(frozen=True)
class _CriticalMove:
    label: str
    quality: str
    eval_before_cp: int
    eval_after_cp: int
    loss_cp: int
    best_move_san: str | None


CRITICAL_ROW = re.compile(
    r"^\|\s*\*\*(?P<label>.+?)\*\*\s*\|\s*(?P<quality>.*?)\s*\|"
    r"\s*(?P<before>[+-]\d+(?:[.,]\d+)?)\s*\|"
    r"\s*(?P<after>[+-]\d+(?:[.,]\d+)?)\s*\|"
    r"\s*(?P<loss>\d+)\s+cp\s*\|\s*(?P<best>.*?)\s*\|$"
)
MOVE_LABEL = re.compile(
    r"^(?P<number>\d+)(?P<separator>\.\.\.|\.)" r"(?P<san>.*?)(?P<annotation>\?\?|\?!|\?|!!)?$"
)
VARIANT_HEADING = re.compile(r"^####\s+(?P<label>.+?)\s*$")
VARIANT_PHASE = re.compile(r"^-\s+\*\*Phase\s*:\*\*\s*(?P<phase>.+?)\s*$")


def _analysis_block(markdown: str) -> str | None:
    try:
        bounds = find_delimited_zone(
            markdown,
            ANALYSIS_START,
            ANALYSIS_END,
            label="d’analyse Chess",
        )
    except DelimitedZoneError as exc:
        raise ChessAnalysisInsightError(str(exc)) from exc
    if bounds is None:
        return None
    return markdown[bounds.start + len(ANALYSIS_START) : bounds.end - len(ANALYSIS_END)]


def _centipawns(value: str) -> int:
    return round(float(value.replace(",", ".")) * 100)


def _critical_moves(block: str) -> list[_CriticalMove]:
    moves: list[_CriticalMove] = []
    for line in block.splitlines():
        match = CRITICAL_ROW.match(line.strip())
        if match is None:
            continue
        best = match.group("best").strip()
        moves.append(
            _CriticalMove(
                label=match.group("label").strip(),
                quality=match.group("quality").strip(),
                eval_before_cp=_centipawns(match.group("before")),
                eval_after_cp=_centipawns(match.group("after")),
                loss_cp=int(match.group("loss")),
                best_move_san=None if best == "—" else best.strip("`"),
            )
        )
    return moves


def _variant_metadata(block: str) -> dict[str, tuple[bool, tuple[str, ...]]]:
    result: dict[str, tuple[bool, tuple[str, ...]]] = {}
    lines = block.splitlines()
    index = 0
    while index < len(lines):
        heading = VARIANT_HEADING.match(lines[index])
        if heading is None:
            index += 1
            continue
        label = heading.group("label").strip()
        phase: bool | None = None
        variation: tuple[str, ...] = ()
        index += 1
        while index < len(lines) and not lines[index].startswith(("#### ", "### ")):
            phase_match = VARIANT_PHASE.match(lines[index])
            if phase_match is not None:
                phase = phase_match.group("phase").strip() == "ouverture"
            if lines[index].strip() == "```text" and index + 1 < len(lines):
                variation = tuple(lines[index + 1].strip().split())
            index += 1
        if phase is not None:
            result[label] = (phase, variation)
    return result


def _categories(quality: str) -> tuple[InsightCategory, ...]:
    categories: list[InsightCategory] = []
    if "??" in quality:
        categories.append("blunder")
    if "!!" in quality:
        categories.append("excellent")
    if "occasion manquée" in quality:
        categories.append("opportunity")
    return tuple(categories)


def parse_analysis_insights(
    markdown: str,
    *,
    game_id: str,
    eco: str | None,
) -> tuple[ChessInsight, ...] | None:
    """Reconstruit les événements d'index depuis le bloc Stockfish visible."""

    block = _analysis_block(markdown)
    if block is None or "Analyse non encore lancée." in block:
        return None
    summary = parse_analysis_summary(markdown)
    if not summary.analysed:
        raise ChessAnalysisInsightError("Bloc d’analyse Stockfish incomplet.")

    phases = _variant_metadata(block)
    insights: list[ChessInsight] = []
    category_counts: dict[InsightCategory, int] = {
        "blunder": 0,
        "excellent": 0,
        "opportunity": 0,
        "motif": 0,
    }
    for move in _critical_moves(block):
        label = MOVE_LABEL.match(move.label)
        if label is None:
            raise ChessAnalysisInsightError(f"Libellé de coup invalide : {move.label}")
        move_number = int(label.group("number"))
        color = cast(
            ChessColor,
            "white" if label.group("separator") == "." else "black",
        )
        ply = move_number * 2 - (1 if color == "white" else 0)
        annotation = label.group("annotation")
        san = label.group("san")
        variant = phases.get(move.label)
        opening_phase = variant[0] if variant is not None else ply <= AnalysisConfig().opening_plies
        principal_variation = variant[1] if variant is not None else ()

        for category in _categories(move.quality):
            category_counts[category] += 1
            subtype = (
                "missed_excellent"
                if category == "opportunity"
                else ("opening" if opening_phase else "middlegame_or_endgame")
            )
            raw_id = f"{game_id}:{ply}:{category}:player"
            insight_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:24]
            insights.append(
                ChessInsight(
                    insight_id=f"analysis:{insight_id}",
                    game_id=game_id,
                    category=category,
                    subtype=subtype,
                    ply=ply,
                    move_number=move_number,
                    color=color,
                    san=san,
                    annotation=annotation,
                    fen_before=None,
                    fen_after=None,
                    eval_before_cp=move.eval_before_cp,
                    eval_after_cp=move.eval_after_cp,
                    loss_cp=move.loss_cp,
                    best_move_san=move.best_move_san,
                    principal_variation=principal_variation,
                    opening_phase=opening_phase,
                    eco=eco,
                    player_role="player",
                )
            )

    if (
        category_counts["blunder"] != summary.blunders
        or category_counts["excellent"] != summary.excellent
        or category_counts["opportunity"] != summary.missed_excellent
    ):
        raise ChessAnalysisInsightError(
            "Le bilan et les coups critiques du bloc Stockfish sont incohérents."
        )
    return tuple(insights)
