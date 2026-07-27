from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal, cast

InsightCategory = Literal["blunder", "excellent", "opportunity", "motif"]
ChessColor = Literal["white", "black"]
PlayerRole = Literal["player", "opponent"]

ALLOWED_CATEGORIES = frozenset({"blunder", "excellent", "opportunity", "motif"})
ALLOWED_COLORS = frozenset({"white", "black"})
ALLOWED_PLAYER_ROLES = frozenset({"player", "opponent"})
CHESS_INSIGHT_SCHEMA_VERSION = 2
SUPPORTED_CHESS_INSIGHT_SCHEMA_VERSIONS = frozenset({1, 2})


class ChessInsightEnvelopeError(ValueError):
    """Signale une enveloppe d'insights invalide."""


class UnsupportedChessInsightSchemaError(ChessInsightEnvelopeError):
    """Signale une version de schéma inconnue."""


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
    played_move_uci: str | None = None
    best_move_uci: str | None = None

    def __post_init__(self) -> None:
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"Catégorie ChessInsight invalide : {self.category}")
        if self.color not in ALLOWED_COLORS:
            raise ValueError(f"Couleur ChessInsight invalide : {self.color}")
        if self.player_role not in ALLOWED_PLAYER_ROLES:
            raise ValueError(f"Rôle ChessInsight invalide : {self.player_role}")

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
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
        if self.played_move_uci is not None:
            payload["played_move_uci"] = self.played_move_uci
        if self.best_move_uci is not None:
            payload["best_move_uci"] = self.best_move_uci
        return payload

    @classmethod
    def from_dict(cls, payload: object) -> ChessInsight:
        if not isinstance(payload, dict):
            raise ChessInsightEnvelopeError("Un insight doit être un objet JSON.")

        def required_string(name: str) -> str:
            value = payload.get(name)
            if not isinstance(value, str):
                raise ChessInsightEnvelopeError(f"Champ insight invalide : {name}")
            return value

        def optional_string(name: str) -> str | None:
            value = payload.get(name)
            if value is not None and not isinstance(value, str):
                raise ChessInsightEnvelopeError(f"Champ insight invalide : {name}")
            return value

        def required_int(name: str) -> int:
            value = payload.get(name)
            if type(value) is not int:
                raise ChessInsightEnvelopeError(f"Champ insight invalide : {name}")
            return value

        opening_phase = payload.get("opening_phase")
        variation = payload.get("principal_variation")
        if not isinstance(opening_phase, bool):
            raise ChessInsightEnvelopeError("Champ insight invalide : opening_phase")
        if not isinstance(variation, list) or not all(
            isinstance(move, str) for move in variation
        ):
            raise ChessInsightEnvelopeError(
                "Champ insight invalide : principal_variation"
            )

        try:
            return cls(
                insight_id=required_string("insight_id"),
                game_id=optional_string("game_id"),
                category=cast(InsightCategory, required_string("category")),
                subtype=optional_string("subtype"),
                ply=required_int("ply"),
                move_number=required_int("move_number"),
                color=cast(ChessColor, required_string("color")),
                san=required_string("san"),
                annotation=optional_string("annotation"),
                fen_before=optional_string("fen_before"),
                fen_after=optional_string("fen_after"),
                eval_before_cp=required_int("eval_before_cp"),
                eval_after_cp=required_int("eval_after_cp"),
                loss_cp=required_int("loss_cp"),
                best_move_san=optional_string("best_move_san"),
                played_move_uci=optional_string("played_move_uci"),
                best_move_uci=optional_string("best_move_uci"),
                principal_variation=tuple(variation),
                opening_phase=opening_phase,
                eco=optional_string("eco"),
                player_role=cast(PlayerRole, required_string("player_role")),
            )
        except ValueError as exc:
            if isinstance(exc, ChessInsightEnvelopeError):
                raise
            raise ChessInsightEnvelopeError(str(exc)) from exc


@dataclass(frozen=True)
class ChessInsightEnvelope:
    schema_version: int
    game_id: str | None
    eco: str | None
    insights: tuple[ChessInsight, ...]
    analysis_metadata: dict[str, object] | None = None
    opening_exit: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if self.schema_version not in SUPPORTED_CHESS_INSIGHT_SCHEMA_VERSIONS:
            raise UnsupportedChessInsightSchemaError(
                f"Version ChessInsight non prise en charge : {self.schema_version}"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "game_id": self.game_id,
            "eco": self.eco,
            "insights": [insight.to_dict() for insight in self.insights],
            **(
                {"analysis_metadata": self.analysis_metadata}
                if self.analysis_metadata is not None
                else {}
            ),
            **(
                {"opening_exit": self.opening_exit}
                if self.opening_exit is not None
                else {}
            ),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, raw_json: str) -> ChessInsightEnvelope:
        try:
            payload: Any = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ChessInsightEnvelopeError("JSON ChessInsight invalide.") from exc
        if not isinstance(payload, dict):
            raise ChessInsightEnvelopeError(
                "L'enveloppe ChessInsight doit être un objet JSON."
            )

        version = payload.get("schema_version")
        if type(version) is not int:
            raise ChessInsightEnvelopeError("schema_version doit être un entier.")
        if version not in SUPPORTED_CHESS_INSIGHT_SCHEMA_VERSIONS:
            raise UnsupportedChessInsightSchemaError(
                f"Version ChessInsight non prise en charge : {version}"
            )

        game_id = payload.get("game_id")
        eco = payload.get("eco")
        raw_insights = payload.get("insights")
        analysis_metadata = payload.get("analysis_metadata")
        opening_exit = payload.get("opening_exit")
        if game_id is not None and not isinstance(game_id, str):
            raise ChessInsightEnvelopeError("game_id doit être une chaîne ou null.")
        if eco is not None and not isinstance(eco, str):
            raise ChessInsightEnvelopeError("eco doit être une chaîne ou null.")
        if not isinstance(raw_insights, list):
            raise ChessInsightEnvelopeError("insights doit être une liste.")
        if analysis_metadata is not None and not isinstance(analysis_metadata, dict):
            raise ChessInsightEnvelopeError(
                "analysis_metadata doit être un objet ou être absent."
            )
        if opening_exit is not None and not isinstance(opening_exit, dict):
            raise ChessInsightEnvelopeError(
                "opening_exit doit être un objet ou être absent."
            )

        return cls(
            schema_version=version,
            game_id=game_id,
            eco=eco,
            insights=tuple(ChessInsight.from_dict(insight) for insight in raw_insights),
            analysis_metadata=analysis_metadata,
            opening_exit=opening_exit,
        )
