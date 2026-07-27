from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import chess
import chess.engine
import pytest

from hanuman.services import chess_analysis_service as service


def _game_analysis(moves=None):
    return service.GameAnalysis(
        white="White",
        black="Black",
        result="*",
        eco="C20",
        opening="King's Pawn",
        engine="Stockfish",
        depth=12,
        moves=moves or [],
        counts={},
        average_centipawn_loss=0,
        worst_move=None,
        turning_point_ply=None,
    )


def test_game_analysis_serialization_and_metadata():
    move = service.MoveAnalysis(
        ply=1,
        move_number=1,
        color="white",
        san="e4",
        uci="e2e4",
        eval_before_cp=20,
        eval_after_cp=10,
        loss_cp=10,
        annotation="",
        classification="normal",
        best_move_san="e4",
        best_move_uci="e2e4",
        principal_variation=["e4"],
        turning_point=False,
        excellent=False,
        missed_excellent=False,
        opening_phase=True,
        depth_reached=14,
    )
    analysis = _game_analysis([move])
    assert analysis.to_dict()["moves"][0]["uci"] == "e2e4"
    assert analysis.analysis_metadata()["depth_reached"] == 14
    assert _game_analysis().analysis_metadata()["depth_reached"] is None


def test_resolve_stockfish_path_prefers_configured_then_raises(tmp_path: Path, monkeypatch):
    engine = tmp_path / "stockfish"
    engine.write_text("", encoding="utf-8")
    assert service.resolve_stockfish_path(str(engine)) == str(engine)

    monkeypatch.setattr(service.shutil, "which", lambda name: None)
    monkeypatch.setattr(service.Path, "is_file", lambda path: False)
    with pytest.raises(FileNotFoundError, match="Stockfish introuvable"):
        service.resolve_stockfish_path()


def test_score_helpers_cover_cp_mate_and_unknown():
    cp = chess.engine.PovScore(chess.engine.Cp(42), chess.WHITE)
    mate = chess.engine.PovScore(chess.engine.Mate(3), chess.WHITE)
    unknown = chess.engine.PovScore(chess.engine.Cp(None), chess.WHITE)
    assert service.score_to_cp(cp, chess.WHITE) == 42
    assert service.score_for_perspective(mate, chess.WHITE) == (3, "mate")
    assert service.score_for_perspective(unknown, chess.WHITE) == (None, "unknown")


def test_pv_conversion_stops_at_illegal_move():
    board = chess.Board()
    legal = chess.Move.from_uci("e2e4")
    illegal = chess.Move.from_uci("e2e5")
    assert service._pv_to_san(board, [legal, illegal]) == ["e4"]


@pytest.mark.parametrize(("score", "zone"), [(100, 1), (99, 0), (-99, 0), (-100, -1)])
def test_position_zones_and_turning_points(score, zone):
    assert service._position_zone(score) == zone
    assert service._is_turning_point(150, -150) is True


def test_material_balance_is_from_requested_perspective():
    board = chess.Board()
    board.remove_piece_at(chess.D8)
    assert service._material_balance(board, chess.WHITE) == 900
    assert service._material_balance(board, chess.BLACK) == -900


@pytest.mark.parametrize(
    ("loss", "best", "second", "delta", "expected"),
    [
        (21, 500, 0, -100, False),
        (0, 300, 100, 0, True),
        (0, 90, -100, -100, True),
        (0, 50, -100, -100, False),
        (0, 300, None, -100, False),
    ],
)
def test_excellent_move_contract(loss, best, second, delta, expected):
    assert service._is_excellent(loss, best, second, delta, service.AnalysisConfig()) is expected


def test_analyzer_context_lifecycle(monkeypatch):
    fake_engine = SimpleNamespace(
        id={"name": "Fakefish"}, quit=lambda: setattr(fake_engine, "quit_called", True)
    )
    monkeypatch.setattr(service, "resolve_stockfish_path", lambda path: "/engine")
    monkeypatch.setattr(service.chess.engine.SimpleEngine, "popen_uci", lambda path: fake_engine)
    analyzer = service.StockfishAnalyzer()

    with analyzer as active:
        assert active.engine_name == "Fakefish"
        assert active.engine is fake_engine

    assert fake_engine.quit_called is True
    assert analyzer.engine is None


def test_analyse_pgn_requires_context_and_valid_game():
    analyzer = service.StockfishAnalyzer()
    with pytest.raises(RuntimeError, match="bloc with"):
        analyzer.analyse_pgn("*")

    analyzer.engine = SimpleNamespace()
    with pytest.raises(ValueError, match="PGN vide"):
        analyzer.analyse_pgn("")


def test_analyse_game_builds_move_events_summary_and_opening_exit():
    pgn = """
[White "Hanuman"]
[Black "Opponent"]
[Result "*"]
[ECO "C20"]
[Opening "King's Pawn"]

1. e4 e5 *
"""
    game = chess.pgn.read_game(__import__("io").StringIO(pgn))
    assert game is not None
    calls = 0

    class FakeEngine:
        def analyse(self, board, limit, multipv=None):
            nonlocal calls
            calls += 1
            mover = chess.WHITE if calls <= 2 else chess.BLACK
            if multipv is not None:
                best_move = next(iter(board.legal_moves))
                return [
                    {
                        "score": chess.engine.PovScore(chess.engine.Cp(300), mover),
                        "pv": [best_move],
                    },
                    {
                        "score": chess.engine.PovScore(chess.engine.Cp(50), mover),
                        "pv": [],
                    },
                ]
            return {
                "score": chess.engine.PovScore(chess.engine.Cp(50), mover),
                "depth": 13,
                "pv": list(board.legal_moves)[:1],
            }

    analyzer = service.StockfishAnalyzer(
        service.AnalysisConfig(depth=12, opening_plies=2, player_name="Hanuman")
    )
    analyzer.engine = FakeEngine()
    analyzer.engine_name = "Fakefish"

    result = analyzer._analyse_game(game)

    assert len(result.moves) == 2
    assert result.moves[0].classification == "blunder"
    assert result.moves[0].missed_excellent is True
    assert result.counts["blunders"] == 2
    assert result.average_centipawn_loss == 250
    assert result.worst_move is not None
    assert result.opening_exit is not None
    assert result.opening_exit.evaluation_perspective == "hanuman-player"
    assert result.engine_configuration == {"multipv": 3, "opening_plies": 2}


def test_analyse_empty_game_uses_defaults_and_black_player_detection():
    game = chess.pgn.Game()
    game.headers["Black"] = "Hanuman"
    analyzer = service.StockfishAnalyzer(service.AnalysisConfig(player_name="hanuman"))
    analyzer.engine = SimpleNamespace()

    result = analyzer._analyse_game(game)

    assert result.moves == []
    assert result.average_centipawn_loss == 0
    assert result.worst_move is None
    assert result.opening_exit is None


def test_module_analyse_pgn_delegates_through_context(monkeypatch):
    expected = _game_analysis()

    class FakeAnalyzer:
        def __init__(self, config):
            self.config = config

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def analyse_pgn(self, pgn):
            assert pgn == "pgn"
            return expected

    monkeypatch.setattr(service, "StockfishAnalyzer", FakeAnalyzer)
    assert service.analyse_pgn("pgn") is expected
