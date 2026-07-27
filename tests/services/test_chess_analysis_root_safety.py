from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from hanuman.config import env
from hanuman.orchestrations import chess_analysis
from hanuman.services import chess_analysis_queue_service as queue
from hanuman.services.chess_analysis_service import (
    GameAnalysis,
    OpeningExitAnalysis,
    StockfishAnalyzer,
)
from hanuman.services.chess_insight_storage_service import parse_insight_block
from hanuman.services.chess_path_safety_service import UnsafeChessDestinationError


class _ForbiddenAnalyzer:
    def analyse_pgn(self, pgn: str) -> None:
        raise AssertionError("Stockfish ne doit pas être appelé")


def _symbolic_root(tmp_path: Path) -> tuple[Path, Path]:
    real = tmp_path / "real"
    symbolic = tmp_path / "symbolic"
    real.mkdir()
    symbolic.symlink_to(real, target_is_directory=True)
    return real, symbolic


def test_analysis_real_root_is_accepted_without_stockfish(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "real"
    root.mkdir()
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(root))

    assert chess_analysis._validated_chess_root() == root
    assert queue.count_analysis_queue() == {"total": 0, "analysed": 0, "pending": 0}
    assert queue.get_analysis_queue_status()["status"] == "idle"


@pytest.mark.parametrize(
    "entry",
    [
        chess_analysis._validated_chess_root,
        queue.get_analysis_queue_status,
        queue.count_analysis_queue,
        queue.start_analysis_queue,
    ],
)
def test_analysis_entries_refuse_symbolic_root_before_writing(
    tmp_path: Path, monkeypatch, entry
) -> None:
    real, symbolic = _symbolic_root(tmp_path)
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(symbolic))

    with pytest.raises(UnsafeChessDestinationError, match="Racine Chess symbolique"):
        entry()

    assert list(real.iterdir()) == []


def test_direct_analysis_refuses_symbolic_root_before_read_or_engine(
    tmp_path: Path,
) -> None:
    real, symbolic = _symbolic_root(tmp_path)
    note = symbolic / "note.md"

    with pytest.raises(UnsafeChessDestinationError, match="Racine Chess symbolique"):
        chess_analysis.analyse_note(
            note,
            cast(StockfishAnalyzer, _ForbiddenAnalyzer()),
            root=symbolic,
        )

    assert list(real.iterdir()) == []


def test_queue_worker_refuses_symbolic_root_before_state_or_engine(tmp_path: Path) -> None:
    real, symbolic = _symbolic_root(tmp_path)

    with pytest.raises(UnsafeChessDestinationError, match="Racine Chess symbolique"):
        queue._run_queue([], symbolic, 12, 25)

    assert list(real.iterdir()) == []


def test_queue_uses_configured_player_and_persists_opening_exit(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "Echecs"
    note = root / "2026/01/game.md"
    note.parent.mkdir(parents=True)
    note.write_text(
        """```pgn
[Event "Queue"]
[White "ConfiguredPlayer"]
[Black "Opponent"]
[Result "1-0"]

1. e4 e5 1-0
```
""",
        encoding="utf-8",
    )
    analysis = GameAnalysis(
        white="ConfiguredPlayer",
        black="Opponent",
        result="1-0",
        eco="C20",
        opening="King's Pawn Game",
        engine="Fixture",
        depth=12,
        moves=[],
        counts={},
        average_centipawn_loss=0.0,
        worst_move=None,
        turning_point_ply=None,
        opening_exit=OpeningExitAnalysis(
            ply=2,
            move_number=1,
            side_to_move="white",
            last_move_san="e5",
            last_move_uci="e7e5",
            fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            evaluation_value=20,
            evaluation_type="centipawn",
            evaluation_perspective="hanuman-player",
            depth_reached=12,
            principal_variation=[],
        ),
    )
    captured = {}

    class FakeAnalyzer:
        def __init__(self, config) -> None:
            captured["player_name"] = config.player_name

        def __enter__(self):
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def analyse_pgn(self, pgn: str) -> GameAnalysis:
            return analysis

    monkeypatch.setattr(env, "CHESS_COM_USERNAME", " ConfiguredPlayer ")
    monkeypatch.setattr(queue, "StockfishAnalyzer", FakeAnalyzer)

    queue._run_queue([note], root, 12, 25)

    envelope = parse_insight_block(note.read_text(encoding="utf-8"))
    assert captured["player_name"] == "ConfiguredPlayer"
    assert envelope is not None
    assert envelope.opening_exit is not None
    assert envelope.opening_exit["evaluation_value"] == 20


def test_analysis_refuses_broken_symbolic_root(tmp_path: Path, monkeypatch) -> None:
    symbolic = tmp_path / "broken"
    symbolic.symlink_to(tmp_path / "missing", target_is_directory=True)
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(symbolic))

    with pytest.raises(UnsafeChessDestinationError, match="Racine Chess symbolique"):
        chess_analysis._validated_chess_root()


def test_analysis_root_is_not_resolved_before_validation(monkeypatch) -> None:
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", "/bin")

    assert chess_analysis._chess_root() == Path("/bin")
    if Path("/bin").is_symlink():
        with pytest.raises(UnsafeChessDestinationError, match="Racine Chess symbolique"):
            chess_analysis._validated_chess_root()
