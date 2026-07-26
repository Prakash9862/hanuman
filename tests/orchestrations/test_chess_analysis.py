from hanuman.orchestrations import chess_analysis as mod
from hanuman.services.chess_analysis_service import GameAnalysis, MoveAnalysis


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
