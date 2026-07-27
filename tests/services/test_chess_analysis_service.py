from pathlib import Path

import chess
import chess.engine

from hanuman.orchestrations.chess_analysis import (
    END_MARKER,
    START_MARKER,
    extract_pgn,
    inject_analysis,
)
from hanuman.services.chess_analysis_service import (
    AnalysisConfig,
    classify_loss,
    score_for_perspective,
)


def test_classify_loss_uses_training_thresholds() -> None:
    config = AnalysisConfig()

    assert classify_loss(250, config) == ("??", "blunder")
    assert classify_loss(200, config) == ("??", "blunder")
    assert classify_loss(199, config) == ("?", "mistake")
    assert classify_loss(100, config) == ("?", "mistake")
    assert classify_loss(99, config) == ("?!", "dubious")
    assert classify_loss(50, config) == ("?!", "dubious")
    assert classify_loss(49, config) == ("", "normal")


def test_extract_pgn_from_markdown() -> None:
    markdown = """# Partie\n\n```pgn\n[Event \"Test\"]\n\n1. e4 e5 *\n```\n"""

    assert extract_pgn(markdown) == '[Event "Test"]\n\n1. e4 e5 *'


def test_inject_analysis_is_idempotent() -> None:
    original = "# Partie\n"
    first = f"{START_MARKER}\n## Analyse 1\n{END_MARKER}"
    second = f"{START_MARKER}\n## Analyse 2\n{END_MARKER}"

    once = inject_analysis(original, first)
    twice = inject_analysis(once, second)

    assert twice.count(START_MARKER) == 1
    assert twice.count(END_MARKER) == 1
    assert "Analyse 1" not in twice
    assert "Analyse 2" in twice


def test_path_import_is_available() -> None:
    assert Path("Parties").name == "Parties"


def test_opening_exit_evaluation_uses_explicit_player_perspective() -> None:
    score = chess.engine.PovScore(chess.engine.Cp(80), chess.WHITE)

    assert score_for_perspective(score, chess.WHITE) == (80, "centipawn")
    assert score_for_perspective(score, chess.BLACK) == (-80, "centipawn")
