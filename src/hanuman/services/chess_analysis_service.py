from __future__ import annotations

import io
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

import chess
import chess.engine
import chess.pgn

MATE_SCORE = 100_000


@dataclass(frozen=True)
class AnalysisConfig:
    engine_path: str | None = None
    depth: int = 18
    multipv: int = 3
    blunder_cp: int = 200
    mistake_cp: int = 100
    dubious_cp: int = 50
    brilliant_gain_cp: int = 200
    excellent_gap_cp: int = 120
    opening_plies: int = 24
    player_name: str | None = None


@dataclass(frozen=True)
class MoveAnalysis:
    ply: int
    move_number: int
    color: str
    san: str
    uci: str
    eval_before_cp: int
    eval_after_cp: int
    loss_cp: int
    annotation: str
    classification: str
    best_move_san: str | None
    best_move_uci: str | None
    principal_variation: list[str]
    turning_point: bool
    excellent: bool
    missed_excellent: bool
    opening_phase: bool
    fen_before: str | None = None
    fen_after: str | None = None
    depth_reached: int | None = None


@dataclass(frozen=True)
class OpeningExitAnalysis:
    ply: int
    move_number: int
    side_to_move: str
    last_move_san: str
    last_move_uci: str
    fen: str
    evaluation_value: int | None
    evaluation_type: str
    evaluation_perspective: str
    depth_reached: int | None
    principal_variation: list[str]


@dataclass(frozen=True)
class GameAnalysis:
    white: str
    black: str
    result: str
    eco: str
    opening: str
    engine: str
    depth: int
    moves: list[MoveAnalysis]
    counts: dict[str, int]
    average_centipawn_loss: float
    worst_move: str | None
    turning_point_ply: int | None
    analysis_schema_version: int = 2
    analysed_at: str | None = None
    evaluation_perspective: str = "side-to-move"
    evaluation_unit: str = "centipawn"
    analysis_limit: dict[str, int] | None = None
    engine_configuration: dict[str, object] | None = None
    opening_exit: OpeningExitAnalysis | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["moves"] = [asdict(move) for move in self.moves]
        return payload

    def analysis_metadata(self) -> dict[str, object]:
        reached_depths = [
            move.depth_reached for move in self.moves if move.depth_reached is not None
        ]
        return {
            "analysis_schema_version": self.analysis_schema_version,
            "engine": self.engine,
            "analysed_at": self.analysed_at,
            "depth_reached": max(reached_depths) if reached_depths else None,
            "analysis_limit": self.analysis_limit,
            "evaluation_perspective": self.evaluation_perspective,
            "evaluation_unit": self.evaluation_unit,
            "engine_configuration": self.engine_configuration,
        }


def resolve_stockfish_path(configured_path: str | None = None) -> str:
    candidates = [configured_path, shutil.which("stockfish"), "/usr/games/stockfish"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise FileNotFoundError(
        "Stockfish introuvable. Installe-le ou définis STOCKFISH_PATH dans .env."
    )


def score_to_cp(score: chess.engine.PovScore, color: chess.Color) -> int:
    value = score.pov(color).score(mate_score=MATE_SCORE)
    return int(value or 0)


def score_for_perspective(
    score: chess.engine.PovScore,
    color: chess.Color,
) -> tuple[int | None, str]:
    """Retourne cp ou distance de mat depuis la perspective explicitement fournie."""

    pov_score = score.pov(color)
    mate = pov_score.mate()
    if mate is not None:
        return int(mate), "mate"
    centipawns = pov_score.score()
    return (
        (int(centipawns), "centipawn") if centipawns is not None else (None, "unknown")
    )


def classify_loss(loss_cp: int, config: AnalysisConfig) -> tuple[str, str]:
    if loss_cp >= config.blunder_cp:
        return "??", "blunder"
    if loss_cp >= config.mistake_cp:
        return "?", "mistake"
    if loss_cp >= config.dubious_cp:
        return "?!", "dubious"
    return "", "normal"


def _pv_to_san(board: chess.Board, pv: list[chess.Move], limit: int = 6) -> list[str]:
    copy = board.copy(stack=False)
    result: list[str] = []
    for move in pv[:limit]:
        if move not in copy.legal_moves:
            break
        result.append(copy.san(move))
        copy.push(move)
    return result


def _position_zone(score_cp: int) -> int:
    if score_cp >= 100:
        return 1
    if score_cp <= -100:
        return -1
    return 0


def _is_turning_point(before_cp: int, after_cp: int) -> bool:
    return _position_zone(before_cp) != _position_zone(after_cp)


def _material_balance(board: chess.Board, color: chess.Color) -> int:
    values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
    }
    own = sum(
        len(board.pieces(piece, color)) * value for piece, value in values.items()
    )
    other = sum(
        len(board.pieces(piece, not color)) * value for piece, value in values.items()
    )
    return own - other


def _is_excellent(
    played_loss_cp: int,
    best_cp: int,
    second_cp: int | None,
    material_delta: int,
    config: AnalysisConfig,
) -> bool:
    if played_loss_cp > 20:
        return False
    unique_gap = (
        second_cp is not None and best_cp - second_cp >= config.excellent_gap_cp
    )
    tactical_gain = best_cp >= config.brilliant_gain_cp
    sound_sacrifice = material_delta < 0 and best_cp >= 80
    return bool(unique_gap and (tactical_gain or sound_sacrifice))


class StockfishAnalyzer:
    """Analyse plusieurs parties avec une seule instance persistante de Stockfish."""

    def __init__(self, config: AnalysisConfig | None = None) -> None:
        self.config = config or AnalysisConfig()
        self.engine: chess.engine.SimpleEngine | None = None
        self.engine_name = "Stockfish"

    def __enter__(self) -> Self:
        engine_path = resolve_stockfish_path(self.config.engine_path)
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.engine_name = str(self.engine.id.get("name", "Stockfish"))
        return self

    def __exit__(self, *_: object) -> None:
        if self.engine is not None:
            self.engine.quit()
            self.engine = None

    def analyse_pgn(self, pgn: str) -> GameAnalysis:
        if self.engine is None:
            raise RuntimeError("StockfishAnalyzer doit être utilisé dans un bloc with")
        game = chess.pgn.read_game(io.StringIO(pgn))
        if game is None:
            raise ValueError("PGN vide ou invalide")
        return self._analyse_game(game)

    def _analyse_game(self, game: chess.pgn.Game) -> GameAnalysis:
        assert self.engine is not None
        cfg = self.config
        board = game.board()
        analysed_moves: list[MoveAnalysis] = []
        opening_exit: OpeningExitAnalysis | None = None
        player_color: chess.Color | None = None
        if cfg.player_name:
            player = cfg.player_name.casefold()
            if game.headers.get("White", "").casefold() == player:
                player_color = chess.WHITE
            elif game.headers.get("Black", "").casefold() == player:
                player_color = chess.BLACK

        for ply, move in enumerate(game.mainline_moves(), start=1):
            mover = board.turn
            san = board.san(move)
            fen_before = board.fen()
            material_before = _material_balance(board, mover)

            infos = self.engine.analyse(
                board,
                chess.engine.Limit(depth=cfg.depth),
                multipv=max(2, cfg.multipv),
            )
            info_list = infos if isinstance(infos, list) else [infos]
            best_info = info_list[0]
            best_cp = score_to_cp(best_info["score"], mover)
            best_pv = list(best_info.get("pv", []))
            principal_variation = _pv_to_san(board, best_pv)
            best_move = best_pv[0] if best_pv else None
            best_move_san = (
                board.san(best_move)
                if best_move is not None and best_move in board.legal_moves
                else None
            )
            second_cp = (
                score_to_cp(info_list[1]["score"], mover)
                if len(info_list) > 1
                else None
            )

            board.push(move)
            fen_after = board.fen()
            played_info = self.engine.analyse(
                board,
                chess.engine.Limit(depth=cfg.depth),
            )
            after_cp = score_to_cp(played_info["score"], mover)
            depth_reached = played_info.get("depth")
            loss_cp = max(0, best_cp - after_cp)
            annotation, classification = classify_loss(loss_cp, cfg)

            material_after = _material_balance(board, mover)
            excellent = _is_excellent(
                loss_cp,
                best_cp,
                second_cp,
                material_after - material_before,
                cfg,
            )
            missed_excellent = (
                not excellent
                and loss_cp >= cfg.mistake_cp
                and second_cp is not None
                and best_cp - second_cp >= cfg.excellent_gap_cp
                and best_cp >= cfg.brilliant_gain_cp
            )
            if excellent:
                annotation = "!!"
                classification = "excellent"

            analysed_moves.append(
                MoveAnalysis(
                    ply=ply,
                    move_number=(ply + 1) // 2,
                    color="white" if mover == chess.WHITE else "black",
                    san=san,
                    uci=move.uci(),
                    eval_before_cp=best_cp,
                    eval_after_cp=after_cp,
                    loss_cp=loss_cp,
                    annotation=annotation,
                    classification=classification,
                    best_move_san=best_move_san,
                    best_move_uci=best_move.uci() if best_move else None,
                    principal_variation=principal_variation,
                    turning_point=_is_turning_point(best_cp, after_cp),
                    excellent=excellent,
                    missed_excellent=missed_excellent,
                    opening_phase=ply <= cfg.opening_plies,
                    fen_before=fen_before,
                    fen_after=fen_after,
                    depth_reached=int(depth_reached)
                    if isinstance(depth_reached, int)
                    else None,
                )
            )
            if (
                ply == min(cfg.opening_plies, game.end().ply())
                and player_color is not None
            ):
                evaluation_value, evaluation_type = score_for_perspective(
                    played_info["score"], player_color
                )
                exit_pv = list(played_info.get("pv", []))
                opening_exit = OpeningExitAnalysis(
                    ply=ply,
                    move_number=(ply + 1) // 2,
                    side_to_move="white" if board.turn == chess.WHITE else "black",
                    last_move_san=san,
                    last_move_uci=move.uci(),
                    fen=fen_after,
                    evaluation_value=(
                        int(evaluation_value) if evaluation_value is not None else None
                    ),
                    evaluation_type=evaluation_type
                    if evaluation_value is not None
                    else "unknown",
                    evaluation_perspective="hanuman-player",
                    depth_reached=(
                        int(depth_reached) if isinstance(depth_reached, int) else None
                    ),
                    principal_variation=_pv_to_san(board, exit_pv),
                )

        significant = [
            move for move in analysed_moves if move.classification != "normal"
        ]
        losses = [move.loss_cp for move in analysed_moves]
        worst = max(analysed_moves, key=lambda item: item.loss_cp, default=None)
        turning = next(
            (move.ply for move in analysed_moves if move.turning_point), None
        )
        counts = {
            "blunders": sum(
                move.classification == "blunder" for move in analysed_moves
            ),
            "mistakes": sum(
                move.classification == "mistake" for move in analysed_moves
            ),
            "dubious": sum(move.classification == "dubious" for move in analysed_moves),
            "excellent": sum(move.excellent for move in analysed_moves),
            "missed_excellent": sum(move.missed_excellent for move in analysed_moves),
            "significant": len(significant),
        }
        worst_move = None
        if worst is not None:
            separator = "." if worst.color == "white" else "..."
            worst_move = f"{worst.move_number}{separator}{worst.san}{worst.annotation}"

        return GameAnalysis(
            white=game.headers.get("White", "White"),
            black=game.headers.get("Black", "Black"),
            result=game.headers.get("Result", "*"),
            eco=game.headers.get("ECO", "UNK"),
            opening=game.headers.get("Opening", "Ouverture inconnue"),
            engine=self.engine_name,
            depth=cfg.depth,
            moves=analysed_moves,
            counts=counts,
            average_centipawn_loss=round(sum(losses) / len(losses), 1)
            if losses
            else 0.0,
            worst_move=worst_move,
            turning_point_ply=turning,
            analysed_at=datetime.now(UTC).isoformat(),
            evaluation_perspective="side-to-move for events; hanuman-player for opening_exit",
            analysis_limit={"depth": cfg.depth},
            engine_configuration={
                "multipv": cfg.multipv,
                "opening_plies": cfg.opening_plies,
            },
            opening_exit=opening_exit,
        )


def analyse_pgn(pgn: str, config: AnalysisConfig | None = None) -> GameAnalysis:
    with StockfishAnalyzer(config) as analyzer:
        return analyzer.analyse_pgn(pgn)
