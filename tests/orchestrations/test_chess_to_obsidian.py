import datetime as dt

import pytest

from hanuman.orchestrations import chess_to_obsidian as mod


class FakeChessService:
    """Service Chess.com factice pour tester l'orchestration sans appels réels."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def get_latest_games(self, username: str, limit: int) -> list[dict]:
        self.calls.append((username, limit))
        base = dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc)

        return [
            {
                "id": "g1",
                "end_time": base,
                "white": "prakasch",
                "black": "Opponent1",
                "result": "win",
                "color": "white",
                "opening_name": "Sicilian Defense",
                "eco": "B20",
                "time_control": "blitz",
                "url": "https://chess.com/game/1",
                "pgn": (
                    '[Event "Game1"]\n'
                    '[White "prakasch"]\n'
                    '[Black "Opponent1"]\n'
                    '[WhiteElo "1800"]\n'
                    '[BlackElo "1750"]\n'
                    '[Opening "Sicilian Defense"]\n'
                    '[Termination "prakasch won by resignation"]\n\n'
                    "1. e4 c5 2. Nf3"
                ),
            },
            {
                "id": "g2",
                "end_time": base + dt.timedelta(days=1),
                "white": "Opponent2",
                "black": "prakasch",
                "result": "loss",
                "color": "black",
                "opening_name": "Sicilian Defense",
                "eco": "B20",
                "time_control": "blitz",
                "url": "https://chess.com/game/2",
                "pgn": (
                    '[Event "Game2"]\n'
                    '[White "Opponent2"]\n'
                    '[Black "prakasch"]\n'
                    '[Opening "Sicilian Defense"]\n\n'
                    "1. e4 c5 2. Nf3 d6"
                ),
            },
        ]


def _sample_game() -> mod.ChessGame:
    return mod._game_from_raw(FakeChessService().get_latest_games("prakasch", 1)[0])


def test_game_note_characterizes_existing_markdown() -> None:
    """Le rendu historique reste protégé pendant l'extraction des vues."""

    note = mod._game_note(_sample_game())

    assert note.startswith("---\ntype: chess-game\ncssclasses:\n")
    assert "  - hanuman-chess\n  - hanuman-chess-game\n" in note
    assert "# ♟️ 2024-01-01 — B20 — Opponent1" in note
    assert "> [!chess] Partie" in note
    assert "## Résumé\n\n| Élément | Détail |" in note
    assert "> [!info]- En-têtes PGN" in note
    assert "> | **WhiteElo** | 1800 |" in note
    assert "> [!note]- PGN complet" in note
    assert '> [Event "Game1"]' in note
    assert "> 1. e4 c5 2. Nf3" in note
    assert "[Ouvrir sur Chess.com](https://chess.com/game/1)" in note
    assert mod.ANALYSIS_START in note
    assert "## Analyse Stockfish" in note
    assert mod.ANALYSIS_END in note


def test_game_note_preserves_existing_analysis_verbatim() -> None:
    existing = (
        f"{mod.ANALYSIS_START}\n"
        "## Analyse Stockfish\n\n"
        "> [!stockfish] Analyse humaine enrichie\n\n"
        "### Ton bilan\n\nAnnotation conservée.\n"
        f"{mod.ANALYSIS_END}"
    )

    note = mod._game_note(_sample_game(), existing)

    assert existing in note
    assert note.count(mod.ANALYSIS_START) == 1
    assert note.count(mod.ANALYSIS_END) == 1


def test_sync_writes_games_and_graph_indexes(tmp_path, monkeypatch) -> None:
    """La synchronisation écrit les parties et les nœuds du graphe Obsidian."""

    obsidian_root = tmp_path / "Echecs"
    fake_service = FakeChessService()

    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(obsidian_root))
    monkeypatch.setattr(mod, "CHESS_USERNAME", "prakasch")
    monkeypatch.setattr(mod, "ChessService", lambda: fake_service)

    result = mod.sync_chess_to_obsidian(limit=50)

    assert fake_service.calls == [("prakasch", 50)]
    assert result == {
        "status": "ok",
        "username": "prakasch",
        "destination": str(obsidian_root),
        "games_received": 2,
        "games_written": 2,
        "analyses_preserved": 0,
        "index_files_written": 7,
        "reset": False,
        "structure": (
            "Echecs/YYYY/MM/date - ECO - adversaire.md + "
            "_Index/Dashboard, Profil et vues thématiques"
        ),
    }

    first_game = obsidian_root / "2024" / "01" / "2024-01-01 - B20 - Opponent1.md"
    second_game = obsidian_root / "2024" / "01" / "2024-01-02 - B20 - Opponent2.md"

    assert first_game.is_file()
    assert second_game.is_file()

    first_content = first_game.read_text(encoding="utf-8")
    assert "type: chess-game" in first_content
    assert "hanuman-chess-game" in first_content
    assert "result: win" in first_content
    assert 'opponent: "Opponent1"' in first_content
    assert "eco: B20" in first_content
    assert "analysis_status: pending" in first_content
    assert "chess/opening/B20" in first_content
    assert "chess/year/2024" in first_content
    assert "chess/month/2024-01" in first_content
    assert "chess/analysis/pending" in first_content
    assert "[[Echecs/_Index/Dashboard|Tableau de bord]]" in first_content
    assert "[[Echecs/_Index/Profil échiquéen|Profil échiquéen]]" in first_content
    assert "[[Echecs/_Index/Ouvertures/B20|B20]]" in first_content
    assert "_Index/Annees" not in first_content
    assert "_Index/Mois" not in first_content
    assert "_Index/Adversaires" not in first_content
    assert "> [!info]- En-têtes PGN" in first_content
    assert "WhiteElo" in first_content
    assert "1800" in first_content
    assert "> [!note]- PGN complet" in first_content
    assert '[Event "Game1"]' in first_content
    assert "## Analyse Stockfish" in first_content
    assert "> [!stockfish] 🟡 Analyse en attente" in first_content
    assert "Analyse non encore lancée." in first_content

    opening_index = obsidian_root / "_Index" / "Ouvertures" / "B20.md"
    dashboard = obsidian_root / "_Index" / "Dashboard.md"
    profile = obsidian_root / "_Index" / "Profil échiquéen.md"

    for path in (opening_index, dashboard, profile):
        assert path.is_file()

    assert "2024-01-02 · B20 · Opponent2 · loss" in opening_index.read_text(encoding="utf-8")
    dashboard_content = dashboard.read_text(encoding="utf-8")
    assert "hanuman-chess-dashboard" in dashboard_content
    assert "[[Echecs/_Index/Ouvertures/B20|B20]]" in dashboard_content
    assert not (obsidian_root / "Dashboard.md").exists()
    assert not (obsidian_root / "_Index/Annees").exists()
    assert not (obsidian_root / "_Index/Mois").exists()
    assert not (obsidian_root / "_Index/Adversaires").exists()
    assert len(list(obsidian_root.glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/*.md"))) == 2


def test_sync_preserves_existing_analysis(tmp_path, monkeypatch) -> None:
    """Une synchronisation sans reset conserve l'analyse Stockfish existante."""

    obsidian_root = tmp_path / "Echecs"
    fake_service = FakeChessService()
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(obsidian_root))
    monkeypatch.setattr(mod, "ChessService", lambda: fake_service)

    mod.sync_chess_to_obsidian(limit=1)
    path = obsidian_root / "2024" / "01" / "2024-01-02 - B20 - Opponent2.md"
    original = path.read_text(encoding="utf-8")
    analysed = original.replace(
        "Analyse non encore lancée.",
        "Analyse déjà calculée.",
    )
    path.write_text(analysed, encoding="utf-8")

    result = mod.sync_chess_to_obsidian(limit=1)

    assert result["analyses_preserved"] == 1
    assert "Analyse déjà calculée." in path.read_text(encoding="utf-8")
    assert len(list(obsidian_root.glob("2024/01/*.md"))) == 1


def test_sync_preserves_legacy_indexes(tmp_path, monkeypatch) -> None:
    obsidian_root = tmp_path / "Echecs"
    legacy_files = {
        obsidian_root / "_Index" / "Annees" / "2024.md": "Année historique",
        obsidian_root / "_Index" / "Mois" / "2024-01.md": "Mois historique",
        obsidian_root / "_Index" / "Adversaires" / "Annotation.md": "Annotation humaine",
    }
    for path, content in legacy_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(obsidian_root))
    monkeypatch.setattr(mod, "ChessService", FakeChessService)

    mod.sync_chess_to_obsidian(limit=1)

    for path, content in legacy_files.items():
        assert path.read_text(encoding="utf-8") == content


def test_sync_delegates_view_generation(tmp_path, monkeypatch) -> None:
    obsidian_root = tmp_path / "Echecs"
    received: list[tuple[object, list[mod.ChessGame]]] = []
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(obsidian_root))
    monkeypatch.setattr(mod, "ChessService", FakeChessService)

    def fake_write_indexes(root, games):
        received.append((root, games))
        return 17

    monkeypatch.setattr(mod, "write_chess_indexes", fake_write_indexes)

    result = mod.sync_chess_to_obsidian(limit=1)

    assert len(received) == 1
    assert received[0][0] == obsidian_root
    assert [game.game_id for game in received[0][1]] == ["g2"]
    assert result["index_files_written"] == 17


def test_sync_refuses_reset_before_calling_chess_service(monkeypatch) -> None:
    monkeypatch.setattr(
        mod,
        "ChessService",
        lambda: pytest.fail("Chess.com ne doit pas être appelé"),
    )

    with pytest.raises(mod.UnsafeChessResetError, match="non destructive"):
        mod.sync_chess_to_obsidian(reset=True)


def test_main_refuses_reset(capsys) -> None:
    with pytest.raises(SystemExit) as raised:
        mod.main(["--reset"])

    assert raised.value.code == 2
    assert "non destructive" in capsys.readouterr().err


def test_main_calls_sync_with_custom_limit(monkeypatch) -> None:
    """main() transmet correctement --limit à l'orchestration."""

    called_with: list[int] = []

    def fake_sync(limit: int) -> dict[str, object]:
        called_with.append(limit)
        return {"status": "ok"}

    monkeypatch.setattr(mod, "sync_chess_to_obsidian", fake_sync)
    mod.main(["--limit", "42"])
    assert called_with == [42]
