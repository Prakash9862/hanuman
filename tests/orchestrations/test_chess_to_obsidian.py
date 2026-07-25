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
                "pgn": '[Event "Game1"]\n1. e4 c5 2. Nf3',
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
                "pgn": '[Event "Game2"]\n1. e4 c5 2. Nf3 d6',
            },
        ]


def test_sync_chess_to_obsidian_writes_notes(tmp_path, monkeypatch) -> None:
    """L'orchestration écrit les parties, les ouvertures et le tableau de bord."""

    obsidian_root = tmp_path / "Echecs"
    fake_service = FakeChessService()

    monkeypatch.setattr(mod, "OBSIDIAN_ROOT", obsidian_root)
    monkeypatch.setattr(mod, "CHESS_USERNAME", "prakasch")
    monkeypatch.setattr(mod, "ChessService", lambda: fake_service)

    result = mod.sync_chess_to_obsidian(limit=50)

    assert fake_service.calls == [("prakasch", 50)]

    assert result == {
        "status": "ok",
        "username": "prakasch",
        "destination": str(obsidian_root),
        "games_received": 2,
        "games_created": 2,
        "games_skipped": 0,
        "openings_updated": 1,
    }

    first_game = obsidian_root / "Parties" / "2024" / "2024-01-01 - B20 - prakasch vs Opponent1.md"
    second_game = obsidian_root / "Parties" / "2024" / "2024-01-02 - B20 - Opponent2 vs prakasch.md"

    assert first_game.is_file()
    assert second_game.is_file()

    first_content = first_game.read_text(encoding="utf-8")
    assert "type: chess-game" in first_content
    assert "result: win" in first_content
    assert "Opponent1" in first_content
    assert '[Event "Game1"]' in first_content

    opening_path = obsidian_root / "Openings" / "B" / "B20 - Sicilian Defense.md"
    assert opening_path.is_file()

    opening_content = opening_path.read_text(encoding="utf-8")
    assert "type: chess-opening" in opening_content
    assert "eco: B20" in opening_content
    assert "games_count: 2" in opening_content
    assert "Victoires :** 1" in opening_content
    assert "Défaites :** 1" in opening_content

    dashboard_path = obsidian_root / "Dashboard.md"
    assert dashboard_path.is_file()

    dashboard_content = dashboard_path.read_text(encoding="utf-8")
    assert 'title: "Chess.com → Obsidian"' in dashboard_content
    assert "games_count: 2" in dashboard_content
    assert "openings_count: 1" in dashboard_content
    assert "B20 · Sicilian Defense" in dashboard_content


def test_main_calls_sync_with_custom_limit(monkeypatch) -> None:
    """main() transmet correctement --limit à l'orchestration."""

    called_with: list[int] = []

    def fake_sync(limit: int) -> dict[str, object]:
        called_with.append(limit)
        return {"status": "ok"}

    monkeypatch.setattr(mod, "sync_chess_to_obsidian", fake_sync)

    mod.main(["--limit", "42"])

    assert called_with == [42]
