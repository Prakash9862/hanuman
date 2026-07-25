import datetime as dt

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
        "index_files_written": 6,
        "reset": False,
        "structure": "Echecs/YYYY/MM/date - ECO - adversaire.md + _Index",
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
    assert "[[_Index/Annees/2024|2024]]" in first_content
    assert "[[_Index/Mois/2024-01|2024-01]]" in first_content
    assert "[[_Index/Ouvertures/B20|B20]]" in first_content
    assert "[[_Index/Adversaires/Opponent1|Opponent1]]" in first_content
    assert "> [!info]- En-têtes PGN" in first_content
    assert "WhiteElo" in first_content
    assert "1800" in first_content
    assert "> [!note]- PGN complet" in first_content
    assert '[Event "Game1"]' in first_content
    assert "## Analyse Stockfish" in first_content
    assert "> [!stockfish] 🟡 Analyse en attente" in first_content
    assert "Analyse non encore lancée." in first_content

    year_index = obsidian_root / "_Index" / "Annees" / "2024.md"
    month_index = obsidian_root / "_Index" / "Mois" / "2024-01.md"
    opening_index = obsidian_root / "_Index" / "Ouvertures" / "B20.md"
    opponent_index = obsidian_root / "_Index" / "Adversaires" / "Opponent1.md"
    dashboard = obsidian_root / "Dashboard.md"

    for path in (year_index, month_index, opening_index, opponent_index, dashboard):
        assert path.is_file()

    assert "2024-01-01 · B20 · Opponent1 · win" in year_index.read_text(encoding="utf-8")
    assert "2024-01-02 · B20 · Opponent2 · loss" in opening_index.read_text(
        encoding="utf-8"
    )
    dashboard_content = dashboard.read_text(encoding="utf-8")
    assert "hanuman-chess-dashboard" in dashboard_content
    assert "[[_Index/Ouvertures/B20|B20]]" in dashboard_content


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


def test_main_calls_sync_with_custom_limit(monkeypatch) -> None:
    """main() transmet correctement --limit à l'orchestration."""

    called_with: list[int] = []

    def fake_sync(limit: int) -> dict[str, object]:
        called_with.append(limit)
        return {"status": "ok"}

    monkeypatch.setattr(mod, "sync_chess_to_obsidian", fake_sync)
    mod.main(["--limit", "42"])
    assert called_with == [42]
