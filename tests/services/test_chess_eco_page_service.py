from __future__ import annotations

import datetime as dt
import hashlib
import subprocess
from pathlib import Path

import pytest
import yaml

from hanuman.models.chess import ChessGame, chess_game_path
from hanuman.models.chess_insight import ChessInsight, ChessInsightEnvelope
from hanuman.services.chess_eco_page_service import (
    SECTION_HEADINGS,
    write_eco_pages,
)
from hanuman.services.chess_insight_storage_service import inject_insight_block

ECOS = (
    "A00",
    "A01",
    "A02",
    "A04",
    "A06",
    "A07",
    "A11",
    "A13",
    "A40",
    "A41",
    "A43",
    "A45",
    "A46",
    "A48",
    "A80",
    "B10",
    "B12",
    "B13",
    "B14",
    "B15",
    "B17",
    "B18",
    "B20",
    "B27",
    "D00",
    "D02",
    "D03",
    "D04",
    "D06",
    "D10",
    "D11",
    "D13",
    "D15",
    "D26",
    "D35",
    "D37",
    "D43",
    "D44",
    "D45",
    "D52",
    "D53",
    "D55",
    "D60",
    "E01",
)
PGN = """[Event "Fixture"]
[Result "1-0"]

1. d4 d5 2. Bf4 Nf6 3. e3 e6 1-0"""


def _game(root: Path, eco: str, index: int, *, result: str = "win") -> ChessGame:
    game = ChessGame(
        game_id=f"{eco}-{index}",
        end_time=dt.datetime(2026, 1, index + 1, tzinfo=dt.UTC),
        white="Joueur",
        black=f"Adversaire-{eco}-{index}",
        result=result,
        color="white",
        opening_name=f"Ouverture {eco}",
        eco=eco,
        time_control="blitz",
        url="",
        pgn="",
    )
    path = chess_game_path(root, game)
    path.parent.mkdir(parents=True, exist_ok=True)
    analysis = (
        """### Ton bilan

- **Moteur :** Fixture
- **Profondeur :** 12
- **Perte moyenne :** 20.0 cp par coup joué

| Qualité | Nombre |
|---|---:|
| `??` Gaffes | 1 |
| `?` Erreurs | 0 |
| `?!` Coups douteux | 0 |
| `!!` Excellents coups | 0 |
| Excellents coups manqués | 2 |"""
        if index == 0
        else "Analyse non encore lancée."
    )
    path.write_text(
        f"""---
type: chess-game
---

```pgn
{PGN}
```

<!-- HANUMAN_CHESS_ANALYSIS_START -->
## Analyse Stockfish

{analysis}
<!-- HANUMAN_CHESS_ANALYSIS_END -->

## Notes humaines
Intouchables.
""",
        encoding="utf-8",
    )
    return game


def _fake_pdf(monkeypatch) -> Path:
    lines = "\n".join(f"{eco} nom officiel {eco} 1.d4 d5 2.Ff4 Cf6 3.e3 e6" for eco in ECOS)
    monkeypatch.setattr(
        "hanuman.services.chess_eco_page_service.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, lines, ""),
    )
    return Path("/fixture/ecomast-codes-eco.pdf")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_industrial_generation_rebuilds_44_ecos_deterministically(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "Echecs"
    games = [
        _game(root, eco, index, result=("win", "draw", "loss")[index % 3])
        for eco in reversed(ECOS)
        for index in range(3)
    ]
    prototypes = []
    for index in range(1, 5):
        suffix = "" if index == 1 else str(index)
        path = root / "_Index/Ouvertures" / f"eco_test{suffix}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"prototype {index}\n", encoding="utf-8")
        prototypes.append(path)
    other_index = root / "_Index/Dashboard.md"
    other_index.write_text("dashboard humain\n", encoding="utf-8")
    protected_before = {path: _digest(path) for path in [*prototypes, other_index]}
    notes_before = {
        chess_game_path(root, game): _digest(chess_game_path(root, game)) for game in games
    }

    first = write_eco_pages(root, games, theory_pdf=_fake_pdf(monkeypatch))
    first_pages = {
        path.name: path.read_bytes()
        for path in (root / "_Index/Ouvertures").glob("[A-E][0-9][0-9].md")
    }
    second = write_eco_pages(root, list(reversed(games)), theory_pdf=_fake_pdf(monkeypatch))
    second_pages = {
        path.name: path.read_bytes()
        for path in (root / "_Index/Ouvertures").glob("[A-E][0-9][0-9].md")
    }

    assert first.pages_written == second.pages_written == 44
    assert first.widgets_generated == 44
    assert first.analysed_games == 44
    assert first.theory_lines_missing == 0
    assert first.ecos_generated == tuple(sorted(ECOS))
    assert first_pages == second_pages
    assert {path: _digest(path) for path in protected_before} == protected_before
    assert {path: _digest(path) for path in notes_before} == notes_before

    ids = set()
    for eco in ECOS:
        content = first_pages[f"{eco}.md"].decode()
        end = content.find("\n---\n", 4)
        metadata = yaml.safe_load(content[4:end])
        assert metadata["games"]["total"] == 3
        assert metadata["games"]["wins"] == 1
        assert metadata["games"]["draws"] == 1
        assert metadata["games"]["losses"] == 1
        assert metadata["stockfish"]["analysed_games"] == 1
        assert [content.find(heading) for heading in SECTION_HEADINGS] == sorted(
            content.find(heading) for heading in SECTION_HEADINGS
        )
        board = metadata["boards"][0]
        assert board["id"] not in ids
        ids.add(board["id"])
        assert board["fen"]
        assert board["pgn"]
        assert "<svg " in content
        assert board["actions"] == [
            "open-scid",
            "open-games",
            "copy-fen",
            "copy-pgn",
            "open-note",
        ]
        assert content.rstrip().endswith("Intouchables.") is False


def test_secondary_threshold_uses_win_rate_without_inventing_lines(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "Echecs"
    games = [_game(root, "D00", index) for index in range(3)]

    report = write_eco_pages(root, games, theory_pdf=_fake_pdf(monkeypatch))
    content = (root / "_Index/Ouvertures/D00.md").read_text(encoding="utf-8")

    assert report.pages_written == 1
    assert "Aucune variante secondaire" in content
    assert "Autres essais · 0 parties" in content
    assert "Aucune récurrence ni aucun échiquier n’est fabriqué" in content


def test_v2_opening_health_and_position_recurrence_use_persisted_data(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "Echecs"
    games = [_game(root, "D00", index) for index in range(3)]
    exit_fen = "rnbqkb1r/ppp2ppp/4pn2/3p4/3P1B2/4P3/PPP2PPP/RN1QKBNR w KQkq - 1 4"
    event_fen = "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2"
    evaluations = (100, 0, -100)
    for index, game in enumerate(games):
        path = chess_game_path(root, game)
        insight = ChessInsight(
            insight_id=f"{game.game_id}:3:blunder:player",
            game_id=game.game_id,
            category="blunder",
            subtype="opening",
            ply=3,
            move_number=2,
            color="white",
            san="Bf4",
            annotation="??",
            fen_before=event_fen if index < 2 else exit_fen,
            fen_after=exit_fen,
            eval_before_cp=100,
            eval_after_cp=-120,
            loss_cp=220,
            best_move_san="Nf3",
            principal_variation=("Nf3", "Nf6"),
            opening_phase=True,
            eco="D00",
            player_role="player",
            played_move_uci="c1f4",
            best_move_uci="g1f3",
        )
        envelope = ChessInsightEnvelope(
            schema_version=2,
            game_id=game.game_id,
            eco="D00",
            insights=(insight,),
            analysis_metadata={"evaluation_unit": "centipawn"},
            opening_exit={
                "ply": 6,
                "move_number": 3,
                "side_to_move": "white",
                "last_move_san": "e6",
                "last_move_uci": "e7e6",
                "fen": exit_fen,
                "evaluation_value": evaluations[index],
                "evaluation_type": "centipawn",
                "evaluation_perspective": "hanuman-player",
                "depth_reached": 18,
                "principal_variation": ["Nf3", "Nf6"],
            },
        )
        path.write_text(
            inject_insight_block(path.read_text(encoding="utf-8"), envelope),
            encoding="utf-8",
        )

    write_eco_pages(root, games, theory_pdf=_fake_pdf(monkeypatch))
    content = (root / "_Index/Ouvertures/D00.md").read_text(encoding="utf-8")
    metadata = yaml.safe_load(content[4 : content.find("\n---\n", 4)])

    assert metadata["health_scope"]["opening_exit_evaluable_games"] == 3
    assert metadata["health_scope"]["opening_exit_average_cp"] == 0.0
    assert metadata["health_scope"]["opening_exit_distribution"] == {
        "favorable": 1,
        "balanced": 1,
        "unfavorable": 1,
    }
    assert metadata["boards"][0]["fen"] == exit_fen
    assert metadata["boards"][0]["position_role"] == "persisted-opening-exit"
    assert "3 parties évaluables sur 3" in content
    assert "Position réellement récurrente · 2 occurrences" in content


def _persist_opening_exit(
    root: Path,
    game: ChessGame,
    *,
    evaluation_type: str,
    evaluation_value: int | None,
) -> None:
    path = chess_game_path(root, game)
    envelope = ChessInsightEnvelope(
        schema_version=2,
        game_id=game.game_id,
        eco=game.eco,
        insights=(),
        analysis_metadata={"evaluation_unit": "centipawn"},
        opening_exit={
            "ply": 6,
            "move_number": 3,
            "side_to_move": "white",
            "last_move_san": "e6",
            "last_move_uci": "e7e6",
            "fen": "rnbqkb1r/ppp2ppp/4pn2/3p4/3P1B2/4P3/PPP2PPP/RN1QKBNR w KQkq - 1 4",
            "evaluation_value": evaluation_value,
            "evaluation_type": evaluation_type,
            "evaluation_perspective": "hanuman-player",
            "depth_reached": 18,
            "principal_variation": [],
        },
    )
    path.write_text(
        inject_insight_block(path.read_text(encoding="utf-8"), envelope),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("evaluation_value", "expected_distribution", "expected_finding"),
    [
        (3, {"favorable": 1, "balanced": 0, "unfavorable": 0}, "généralement favorable"),
        (-3, {"favorable": 0, "balanced": 0, "unfavorable": 1}, "position défavorable"),
    ],
)
def test_mate_opening_exit_is_classified_by_sign_and_never_as_cp(
    tmp_path: Path,
    monkeypatch,
    evaluation_value: int,
    expected_distribution: dict[str, int],
    expected_finding: str,
) -> None:
    root = tmp_path / "Echecs"
    game = _game(root, "D00", 0)
    _persist_opening_exit(root, game, evaluation_type="mate", evaluation_value=evaluation_value)

    write_eco_pages(root, [game], theory_pdf=_fake_pdf(monkeypatch))
    content = (root / "_Index/Ouvertures/D00.md").read_text(encoding="utf-8")
    metadata = yaml.safe_load(content[4 : content.find("\n---\n", 4)])
    health = metadata["health_scope"]

    assert health["opening_exit_evaluable_games"] == 1
    assert health["opening_exit_average_cp"] is None
    assert health["opening_exit_median_cp"] is None
    assert health["opening_exit_distribution"] == expected_distribution
    assert health["opening_exit_mate_positions"] == {
        "favorable": int(evaluation_value > 0),
        "unfavorable": int(evaluation_value < 0),
    }
    assert expected_finding in content
    assert "Aucune évaluation en centipions" in content


def test_mixed_cp_mate_and_unknown_keep_cp_statistics_and_evaluable_coverage_separate(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "Echecs"
    games = [_game(root, "D00", index) for index in range(3)]
    for game, evaluation_type, value in zip(
        games,
        ("centipawn", "mate", "unknown"),
        (100, 3, None),
        strict=True,
    ):
        _persist_opening_exit(
            root,
            game,
            evaluation_type=evaluation_type,
            evaluation_value=value,
        )

    write_eco_pages(root, games, theory_pdf=_fake_pdf(monkeypatch))
    content = (root / "_Index/Ouvertures/D00.md").read_text(encoding="utf-8")
    metadata = yaml.safe_load(content[4 : content.find("\n---\n", 4)])
    health = metadata["health_scope"]

    assert health["opening_exit_evaluable_games"] == 2
    assert health["opening_exit_coverage_percent"] == 66.7
    assert health["opening_exit_average_cp"] == 100.0
    assert health["opening_exit_median_cp"] == 100.0
    assert health["opening_exit_distribution"] == {
        "favorable": 2,
        "balanced": 0,
        "unfavorable": 0,
    }
    assert health["opening_exit_mate_positions"] == {
        "favorable": 1,
        "unfavorable": 0,
    }
    assert "2 parties évaluables sur 3" in content
    assert "sur **1 évaluation(s) en centipions**" in content
