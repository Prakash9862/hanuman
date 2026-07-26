from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

InsightCategory = Literal["blunder", "excellent", "opportunity", "motif"]
ChessColor = Literal["white", "black"]
PlayerRole = Literal["player", "opponent"]

ALLOWED_CATEGORIES = frozenset({"blunder", "excellent", "opportunity", "motif"})
ALLOWED_COLORS = frozenset({"white", "black"})
ALLOWED_PLAYER_ROLES = frozenset({"player", "opponent"})


@dataclass(frozen=True)
class ChessInsight:
    insight_id: str
    game_id: str | None
    category: InsightCategory
    subtype: str | None
    ply: int
    move_number: int
    color: ChessColor
    san: str
    annotation: str | None
    fen_before: str | None
    fen_after: str | None
    eval_before_cp: int
    eval_after_cp: int
    loss_cp: int
    best_move_san: str | None
    principal_variation: tuple[str, ...]
    opening_phase: bool
    eco: str | None
    player_role: PlayerRole

    def __post_init__(self) -> None:
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"Catégorie ChessInsight invalide : {self.category}")
        if self.color not in ALLOWED_COLORS:
            raise ValueError(f"Couleur ChessInsight invalide : {self.color}")
        if self.player_role not in ALLOWED_PLAYER_ROLES:
            raise ValueError(f"Rôle ChessInsight invalide : {self.player_role}")

    def to_dict(self) -> dict[str, object]:
        return {
            "insight_id": self.insight_id,
            "game_id": self.game_id,
            "category": self.category,
            "subtype": self.subtype,
            "ply": self.ply,
            "move_number": self.move_number,
            "color": self.color,
            "san": self.san,
            "annotation": self.annotation,
            "fen_before": self.fen_before,
            "fen_after": self.fen_after,
            "eval_before_cp": self.eval_before_cp,
            "eval_after_cp": self.eval_after_cp,
            "loss_cp": self.loss_cp,
            "best_move_san": self.best_move_san,
            "principal_variation": list(self.principal_variation),
            "opening_phase": self.opening_phase,
            "eco": self.eco,
            "player_role": self.player_role,
        }
