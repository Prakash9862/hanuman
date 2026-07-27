from pathlib import Path
from typing import cast

import pytest

from hanuman.orchestrations import chess_analysis as mod
from hanuman.services.chess_analysis_service import (
    GameAnalysis,
    MoveAnalysis,
    StockfishAnalyzer,
)
from hanuman.services.chess_insight_storage_service import (
    INSIGHTS_END,
    INSIGHTS_START,
    parse_insight_block,
)


def _fixture_analysis() -> GameAnalysis:
    move = MoveAnalysis(
        ply=1,
        move_number=1,
        color="white",
        san="e4",
        uci="e2e4",
        eval_before_cp=20,
        eval_after_cp=15,
        loss_cp=5,
        annotation="",
        classification="normal",
        best_move_san="e4",
        best_move_uci="e2e4",
        principal_variation=[],
        turning_point=False,
        excellent=False,
        missed_excellent=False,
        opening_phase=True,
    )
    return GameAnalysis(
        white=mod.CHESS_USERNAME,
        black="Opponent",
        result="1-0",
        eco="C20",
        opening="King's Pawn Game",
        engine="Stockfish Fixture",
        depth=18,
        moves=[move],
        counts={},
        average_centipawn_loss=5.0,
        worst_move="1.e4",
        turning_point_ply=None,
    )


def test_render_analysis_markdown_characterization() -> None:
    expected = f"""{mod.START_MARKER}
## Analyse Stockfish

### Ton bilan

- **Moteur :** Stockfish Fixture
- **Profondeur :** 18
- **Perte moyenne :** 5.0 cp par coup joué
- **Pire coup :** 1.e4
- **Moment de bascule :** aucune bascule détectée

| Qualité | Nombre |
|---|---:|
| `??` Gaffes | 0 |
| `?` Erreurs | 0 |
| `?!` Coups douteux | 0 |
| `!!` Excellents coups | 0 |
| Excellents coups manqués | 0 |

### Tes coups critiques

Aucun de tes coups ne franchit les seuils critiques actuels.

### Variantes critiques

Aucune variante critique disponible.
### Faits marquants de l’adversaire

Aucune gaffe ni coup excellent adverse détecté.

### Seuils utilisés

- `??` : perte d’au moins 200 cp
- `?` : perte de 100 à 199 cp
- `?!` : perte de 50 à 99 cp
- `!!` : coup quasi unique, tactique ou sacrifice correct détecté avec forte confiance

{mod.END_MARKER}"""

    assert mod.render_analysis_markdown(_fixture_analysis()) == expected


def test_inject_analysis_remains_idempotent() -> None:
    rendered = mod.render_analysis_markdown(_fixture_analysis())

    once = mod.inject_analysis("# Partie\n", rendered)
    twice = mod.inject_analysis(once, rendered)

    assert twice == once


@pytest.mark.parametrize(
    "markdown",
    [
        f"{mod.START_MARKER}\nseul",
        f"seul\n{mod.END_MARKER}",
        f"{mod.START_MARKER}\na\n{mod.START_MARKER}\nb\n{mod.END_MARKER}",
        f"{mod.START_MARKER}\na\n{mod.END_MARKER}\nb\n{mod.END_MARKER}",
        f"{mod.END_MARKER}\n{mod.START_MARKER}",
    ],
)
def test_analysis_markers_are_strict_and_never_modified(markdown: str) -> None:
    with pytest.raises(mod.ChessAnalysisBlockError):
        mod.inject_analysis(markdown, f"{mod.START_MARKER}\nnew\n{mod.END_MARKER}")
    assert markdown == markdown


def _critical_analysis() -> GameAnalysis:
    moves = [
        MoveAnalysis(
            ply=1,
            move_number=1,
            color="white",
            san="e4",
            uci="e2e4",
            eval_before_cp=200,
            eval_after_cp=195,
            loss_cp=5,
            annotation="!!",
            classification="excellent",
            best_move_san="e4",
            best_move_uci="e2e4",
            principal_variation=["e4", "e5"],
            turning_point=False,
            excellent=True,
            missed_excellent=False,
            opening_phase=True,
        ),
        MoveAnalysis(
            ply=2,
            move_number=1,
            color="black",
            san="c5",
            uci="c7c5",
            eval_before_cp=100,
            eval_after_cp=-150,
            loss_cp=250,
            annotation="??",
            classification="blunder",
            best_move_san="e5",
            best_move_uci="e7e5",
            principal_variation=["e5", "Nf3"],
            turning_point=True,
            excellent=False,
            missed_excellent=True,
            opening_phase=True,
        ),
    ]
    return GameAnalysis(
        white="Opponent",
        black=mod.CHESS_USERNAME,
        result="0-1",
        eco="B20",
        opening="Sicilian Defense",
        engine="Fixture",
        depth=18,
        moves=moves,
        counts={},
        average_centipawn_loss=127.5,
        worst_move="1...c5??",
        turning_point_ply=2,
    )


class FakeAnalyzer:
    def __init__(self, analysis: GameAnalysis) -> None:
        self.analysis = analysis
        self.pgns: list[str] = []

    def analyse_pgn(self, pgn: str) -> GameAnalysis:
        self.pgns.append(pgn)
        return self.analysis


def _visible_analysis(markdown: str) -> str:
    before, rest = markdown.split(mod.START_MARKER, 1)
    body, _ = rest.split(mod.END_MARKER, 1)
    return mod.START_MARKER + body + mod.END_MARKER


def test_analyse_note_persists_structured_insights_atomically(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = tmp_path / "partie.md"
    personal_notes = """## Notes personnelles

- Garder [[ce lien]].
- Préserver les accents : échec, défense sicilienne.
"""
    original = f"""---
type: chess-game
game_id: "game-42"
eco: B20
color: black
---

> [!note]- PGN complet
>
> ```pgn
> [Event "Fixture"]
>
> 1. e4 c5
> ```

{personal_notes}"""
    path.write_text(original, encoding="utf-8")
    analyzer = FakeAnalyzer(_critical_analysis())
    real_atomic_write = mod.atomic_write_text
    atomic_calls: list[Path] = []

    def spy_atomic_write(target: Path, content: str) -> None:
        atomic_calls.append(target)
        real_atomic_write(target, content)

    monkeypatch.setattr(mod, "atomic_write_text", spy_atomic_write)

    result = mod.analyse_note(path, cast(StockfishAnalyzer, analyzer))
    first = path.read_text(encoding="utf-8")
    first_visible = _visible_analysis(first)
    first_envelope = parse_insight_block(first)
    mod.analyse_note(path, cast(StockfishAnalyzer, analyzer))
    second = path.read_text(encoding="utf-8")

    assert result == analyzer.analysis
    assert analyzer.pgns == [
        '[Event "Fixture"]\n\n1. e4 c5',
        '[Event "Fixture"]\n\n1. e4 c5',
    ]
    assert atomic_calls == [path, path]
    assert first == second
    assert _visible_analysis(second) == first_visible
    assert personal_notes in second
    assert '[Event "Fixture"]' in second
    assert second.startswith(original.split(personal_notes, 1)[0])
    assert second.count(INSIGHTS_START) == 1
    assert second.count(INSIGHTS_END) == 1
    assert first_envelope is not None
    assert first_envelope.game_id == "game-42"
    assert first_envelope.eco == "B20"
    assert [(item.category, item.player_role) for item in first_envelope.insights] == [
        ("excellent", "opponent"),
        ("blunder", "player"),
        ("opportunity", "player"),
    ]
    assert all(item.category != "motif" for item in first_envelope.insights)
