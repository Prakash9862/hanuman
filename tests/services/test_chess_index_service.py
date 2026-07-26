import datetime as dt
from pathlib import Path

from hanuman.models.chess import ChessGame
from hanuman.services.chess_index_service import write_chess_indexes


def _games() -> list[ChessGame]:
    first = ChessGame(
        game_id="g1",
        end_time=dt.datetime(2024, 1, 1, 12, tzinfo=dt.timezone.utc),
        white="prakasch",
        black="Opponent1",
        result="win",
        color="white",
        opening_name="Sicilian Defense",
        eco="B20",
        time_control="blitz",
        url="https://chess.com/game/1",
        pgn="1. e4 c5",
    )
    second = ChessGame(
        game_id="g2",
        end_time=dt.datetime(2024, 1, 2, 12, tzinfo=dt.timezone.utc),
        white="Opponent2",
        black="prakasch",
        result="loss",
        color="black",
        opening_name="Sicilian Defense",
        eco="B20",
        time_control="blitz",
        url="https://chess.com/game/2",
        pgn="1. e4 c5 2. Nf3 d6",
    )
    return [second, first]


def _markdown_files(root: Path) -> dict[Path, str]:
    return {
        path.relative_to(root): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*.md"))
    }


def test_write_chess_indexes_preserves_current_views(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"

    written = write_chess_indexes(root, _games())

    assert written == 6
    expected_paths = {
        Path("Dashboard.md"),
        Path("_Index/Annees/2024.md"),
        Path("_Index/Mois/2024-01.md"),
        Path("_Index/Ouvertures/B20.md"),
        Path("_Index/Adversaires/Opponent1.md"),
        Path("_Index/Adversaires/Opponent2.md"),
    }
    assert set(_markdown_files(root)) == expected_paths

    dashboard = (root / "Dashboard.md").read_text(encoding="utf-8")
    assert dashboard.startswith("---\ntype: chess-dashboard\ncssclasses:\n")
    assert "  - hanuman-chess-dashboard\n" in dashboard
    assert "# ♛ Tableau de bord Échecs" in dashboard
    assert "> [!chess] Bibliothèque Caïssa" in dashboard
    assert "> **2 parties** · **1 ouvertures** · **2 adversaires**  " in dashboard
    assert "> 🟢 1 victoires · 🟡 0 nulles · 🔴 1 défaites" in dashboard
    assert "[[_Index/Annees/2024|2024]]" in dashboard
    assert "[[_Index/Mois/2024-01|2024-01]]" in dashboard
    assert "[[_Index/Ouvertures/B20|B20]]" in dashboard
    assert dashboard.index("2024-01-02 · B20") < dashboard.index("2024-01-01 · B20")

    opening = (root / "_Index/Ouvertures/B20.md").read_text(encoding="utf-8")
    assert "type: chess-index" in opening
    assert "  - hanuman-index-opening" in opening
    assert "index_kind: opening" in opening
    assert 'index_key: "B20"' in opening
    assert "# B20 — Sicilian Defense" in opening
    assert "> [!chess] Vue d’ensemble" in opening
    assert "> 🏠 [[Dashboard|Retour au tableau de bord]]" in opening
    assert opening.index("2024-01-02 · B20") < opening.index("2024-01-01 · B20")


def test_write_chess_indexes_is_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"

    write_chess_indexes(root, _games())
    first_generation = _markdown_files(root)
    write_chess_indexes(root, _games())

    assert _markdown_files(root) == first_generation


def test_write_chess_indexes_preserves_unknown_human_file(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    human_file = root / "_Index" / "Mes annotations.md"
    human_file.parent.mkdir(parents=True)
    human_file.write_text("Ne pas supprimer cette note.", encoding="utf-8")

    write_chess_indexes(root, _games())

    assert human_file.read_text(encoding="utf-8") == "Ne pas supprimer cette note."
