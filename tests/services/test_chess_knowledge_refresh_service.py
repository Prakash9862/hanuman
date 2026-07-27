import hashlib
from pathlib import Path

import pytest

from hanuman.services.chess_analysis_service import StockfishAnalyzer
from hanuman.services.chess_view_rebuild_service import refresh_chess_knowledge


def _note(index: int, *, analysed: bool) -> str:
    day = index % 28 + 1
    analysis = (
        """## Analyse Stockfish

### Ton bilan

- **Moteur :** Stockfish Fixture
- **Profondeur :** 12
- **Perte moyenne :** 10.0 cp par coup joué

| Qualité | Nombre |
|---|---:|
| `??` Gaffes | 0 |
| `?` Erreurs | 0 |
| `?!` Coups douteux | 0 |
| `!!` Excellents coups | 0 |
| Excellents coups manqués | 0 |"""
        if analysed
        else "## Analyse Stockfish\n\nAnalyse non encore lancée."
    )
    return f"""---
type: chess-game
date: 2024-01-{day:02d}
game_id: "g{index}"
result: win
color: white
opponent: "Adversaire {index}"
white: "Joueur"
black: "Adversaire {index}"
eco: B20
opening: "Défense sicilienne"
time_control: "blitz"
chess_url: "https://example.test/{index}"
---

# Partie

<!-- HANUMAN_CHESS_ANALYSIS_START -->
{analysis}
<!-- HANUMAN_CHESS_ANALYSIS_END -->

## Notes personnelles

Texte humain {index}.
"""


def _write_note(root: Path, index: int, *, analysed: bool) -> Path:
    day = index % 28 + 1
    path = root / f"2024/01/2024-01-{day:02d} - B20 - Adversaire {index}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_note(index, analysed=analysed), encoding="utf-8")
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_refresh_makes_45_plus_483_analyses_visible_without_rerunning_stockfish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "Echecs"
    notes = [_write_note(root, index, analysed=index < 528) for index in range(997)]
    before = {path: _digest(path) for path in notes}

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Stockfish ne doit pas être relancé.")

    monkeypatch.setattr(StockfishAnalyzer, "__init__", forbidden)

    first = refresh_chess_knowledge(root)
    first_files = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*.md")
        if "_Index" in path.parts
    }
    second = refresh_chess_knowledge(root)
    second_files = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*.md")
        if "_Index" in path.parts
    }

    assert first.notes_discovered == 997
    assert first.analyses_valid == 45 + 483 == 528
    assert first.games_pending == 469
    assert first.analyses_invalid == 0
    assert first.analyses_orphaned == 0
    assert first.opening_indexes_written == 0
    assert second.analyses_valid == first.analyses_valid
    assert second_files == first_files
    assert {path: _digest(path) for path in notes} == before
    profile = (root / "_Index/Profil échiquéen.md").read_text(encoding="utf-8")
    dashboard = (root / "_Index/Dashboard.md").read_text(encoding="utf-8")
    assert "**Analyse :** 528 analysées · 469 en attente · 0 illisibles" in profile
    assert "**528 parties analysées sur 997**" in profile
    assert "**528 parties analysées sur 997**" in dashboard


def test_refresh_ignores_an_orphaned_analysis(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    _write_note(root, 1, analysed=True)
    orphan = root / "2024/01/2024-01-03 - B20 - Orpheline.md"
    orphan.write_text(
        _note(2, analysed=True).replace('game_id: "g2"\n', ""),
        encoding="utf-8",
    )

    report = refresh_chess_knowledge(root)

    assert report.notes_discovered == 2
    assert report.notes_usable == 1
    assert report.analyses_valid == 1
    assert report.analyses_orphaned == 1
    assert report.games_pending == 0
