from __future__ import annotations

import io
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["moves"] = [asdict(move) for move in self.moves]
        return payload


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
    if value is None:
        return 0
    return int(value)


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


def _is_turning_point(before_cp: int, after_cp: int) -> bool:
    before_zone = 1 if before_cp >= 100 else -1 if before_cp <= -100 else 0
    after_zone = 1 if after_cp >= 100 else -1 if after_cp <= -100 else 0
    return before_zone != after_zone


def _is_excellent(
    played_loss_cp: int,
    best_cp: int,
    second_cp: int | None,
    material_delta: int,
    config: AnalysisConfig,
) -> bool:
    if played_loss_cp > 20:
        return False
    unique_gap = second_cp is not None and best_cp - second_cp >= config.excellent_gap_cp
    tactical_gain = best_cp >= config.brilliant_gain_cp
    sound_sacrifice = material_delta < 0 and best_cp >= 80
    return bool(unique_gap and (tactical_gain or sound_sacrifice))


def _material_balance(board: chess.Board, color: chess.Color) -> int:
    values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
    }
    own = sum(len(board.pieces(piece, color)) * value for piece, value in values.items())
    other = sum(
        len(board.pieces(piece, not color)) * value for piece, value in values.items()
    )
    return own - other


def analyse_pgn(pgn: str, config: AnalysisConfig | None = None) -> GameAnalysis:
    cfg = config or AnalysisConfig()
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        raise ValueError("PGN vide ou invalide")

    engine_path = resolve_stockfish_path(cfg.engine_path)
    board = game.board()
    analysed_moves: list[MoveAnalysis] = []

    with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
        engine_name = str(engine.id.get("name", "Stockfish"))
        for ply, move in enumerate(game.mainline_moves(), start=1):
            mover = board.turn
            san = board.san(move)
            material_before = _material_balance(board, mover)

            infos = engine.analyse(
                board,
                chess.engine.Limit(depth=cfg.depth),
                multipv=max(2, cfg.multipv),
            )
            if isinstance(infos, dict):
                infos = [infos]

            best_info = infos[0]
            best_cp = score_to_cp(best_info["score"], mover)
            best_pv = list(best_info.get("pv", []))
            best_move = best_pv[0] if best_pv else None
            best_move_san = board.san(best_move) if best_move in board.legal_moves else None
            second_cp = (
                score_to_cp(infos[1]["score"], mover) if len(infos) > 1 else None
            )

            board.push(move)
            played_info = engine.analyse(board, chess.engine.Limit(depth=cfg.depth))
            after_cp = score_to_cp(played_info["score"], mover)
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
                    principal_variation=_pv_to_san(board.copy(stack=False), []),
                    turning_point=_is_turning_point(best_cp, after_cp),
                    excellent=excellent,
                    missed_excellent=missed_excellent,
                    opening_phase=ply <= cfg.opening_plies,
                )
            )

    significant = [move for move in analysed_moves if move.classification != "normal"]
    losses = [move.loss_cp for move in analysed_moves]
    worst = max(analysed_moves, key=lambda item: item.loss_cp, default=None)
    turning = next((move.ply for move in analysed_moves if move.turning_point), None)
    counts = {
        "blunders": sum(move.classification == "blunder" for move in analysed_moves),
        "mistakes": sum(move.classification == "mistake" for move in analysed_moves),
        "dubious": sum(move.classification == "dubious" for move in analysed_moves),
        "excellent": sum(move.excellent for move in analysed_moves),
        "missed_excellent": sum(move.missed_excellent for move in analysed_moves),
        "significant": len(significant),
    }

    return GameAnalysis(
        white=game.headers.get("White", "White"),
        black=game.headers.get("Black", "Black"),
        result=game.headers.get("Result", "*"),
        eco=game.headers.get("ECO", "UNK"),
        opening=game.headers.get("Opening", "Ouverture inconnue"),
        engine=engine_name,
        depth=cfg.depth,
        moves=analysed_moves,
        counts=counts,
        average_centipawn_loss=round(sum(losses) / len(losses), 1) if losses else 0.0,
        worst_move=(f"{worst.move_number}{'.' if worst.color == 'white' else '...'}{worst.san}{worst.annotation}" if worst else None),
        turning_point_ply=turning,
    )
