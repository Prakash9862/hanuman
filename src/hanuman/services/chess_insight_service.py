from __future__ import annotations

import hashlib
from typing import Literal, cast

from hanuman.models.chess_insight import (
    ChessColor,
    ChessInsight,
    InsightCategory,
    PlayerRole,
)
from hanuman.services.chess_analysis_service import GameAnalysis, MoveAnalysis


def _derived_game_key(analysis: GameAnalysis) -> str:
    moves = "|".join(f"{move.ply}:{move.san}" for move in analysis.moves)
    source = f"{analysis.white}|{analysis.black}|{analysis.result}|{analysis.eco}|{moves}"
    return f"derived-{hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]}"


def _insight_id(
    analysis: GameAnalysis,
    move: MoveAnalysis,
    category: InsightCategory,
    role: PlayerRole,
    game_id: str | None,
) -> str:
    game_key = game_id or _derived_game_key(analysis)
    return f"{game_key}:{move.ply}:{category}:{role}"


def _subtype(move: MoveAnalysis, category: InsightCategory) -> str:
    if category == "opportunity":
        return "missed_excellent"
    return "opening" if move.opening_phase else "middlegame_or_endgame"


def _build_insight(
    analysis: GameAnalysis,
    move: MoveAnalysis,
    category: InsightCategory,
    *,
    player_color: Literal["white", "black"],
    game_id: str | None,
    eco: str | None,
) -> ChessInsight:
    color = cast(ChessColor, move.color)
    role: PlayerRole = "player" if color == player_color else "opponent"
    return ChessInsight(
        insight_id=_insight_id(analysis, move, category, role, game_id),
        game_id=game_id,
        category=category,
        subtype=_subtype(move, category),
        ply=move.ply,
        move_number=move.move_number,
        color=color,
        san=move.san,
        annotation=move.annotation or None,
        fen_before=move.fen_before,
        fen_after=move.fen_after,
        eval_before_cp=move.eval_before_cp,
        eval_after_cp=move.eval_after_cp,
        loss_cp=move.loss_cp,
        best_move_san=move.best_move_san,
        principal_variation=tuple(move.principal_variation),
        opening_phase=move.opening_phase,
        eco=eco if eco is not None else analysis.eco,
        player_role=role,
        played_move_uci=move.uci,
        best_move_uci=move.best_move_uci,
    )


def build_chess_insights(
    analysis: GameAnalysis,
    *,
    player_color: Literal["white", "black"],
    game_id: str | None = None,
    eco: str | None = None,
) -> tuple[ChessInsight, ...]:
    """Construit des événements déterministes directement depuis les coups analysés."""

    insights: list[ChessInsight] = []
    seen_ids: set[str] = set()
    for move in sorted(analysis.moves, key=lambda item: item.ply):
        categories: list[InsightCategory] = []
        if move.classification == "blunder":
            categories.append("blunder")
        if move.excellent or move.classification == "excellent":
            categories.append("excellent")
        if move.missed_excellent:
            categories.append("opportunity")

        for category in categories:
            insight = _build_insight(
                analysis,
                move,
                category,
                player_color=player_color,
                game_id=game_id,
                eco=eco,
            )
            if insight.insight_id not in seen_ids:
                insights.append(insight)
                seen_ids.add(insight.insight_id)

    return tuple(insights)
