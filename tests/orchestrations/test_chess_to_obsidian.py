import datetime as dt
from pathlib import Path
from types import SimpleNamespace

from hanuman.orchestrations import chess_to_obsidian as mod


class FakeChessService:
    """Service Chess.com factice pour tester l'orchestration sans appels réels."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def get_latest_games(self, username: str, limit: int) -> list[dict]:
        self.calls.append((username, limit))
        base = dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc)

        # Deux parties avec la même ouverture (B20 Sicilian Defense)
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


def test_sync_chess_to_obsidian_writes_notes(tmp_path, monkeypatch, capsys) -> None:
    """sync_chess_to_obsidian doit écrire les fichiers Markdown attendus."""

    # 1) Rediriger Path(...) vers un dossier de test
    #    → /home/.../Echecs devient tmp_path / "Echecs"
    def fake_path(_path_str: str) -> Path:
        return tmp_path / "Echecs"

    monkeypatch.setattr(mod, "Path", fake_path)

    # 2) Mock du ChessService
    fake_service = FakeChessService()
    monkeypatch.setattr(mod, "ChessService", lambda: fake_service)

    # 3) Faux settings avec un username connu
    fake_settings = SimpleNamespace(chess_com_username="prakasch")
    monkeypatch.setattr(mod, "settings", fake_settings)

    # 4) Appel de l'orchestration
    mod.sync_chess_to_obsidian(limit=50)

    # 5) Vérifications sur le service appelé
    assert fake_service.calls == [("prakasch", 50)]

    obsidian_root = tmp_path / "Echecs"
    openings_dir = obsidian_root / "Openings"

    # 6) Overview.md doit exister
    overview_path = obsidian_root / "Overview.md"
    assert overview_path.is_file()

    overview_content = overview_path.read_text(encoding="utf-8")
    # Une seule ouverture (B20 Sicilian Defense), 2 parties
    assert "openings_count: 1" in overview_content
    assert "B20 Sicilian Defense (2 parties)" in overview_content

    # 7) Fichier d'ouverture pour B20 Sicilian Defense
    slug = mod._slugify("B20 Sicilian Defense")
    opening_path = openings_dir / f"{slug}.md"
    assert opening_path.is_file()

    opening_content = opening_path.read_text(encoding="utf-8")

    # Métadonnées YAML
    assert 'title: "B20 Sicilian Defense"' in opening_content
    assert "tags:" in opening_content
    assert "games_count: 2" in opening_content

    # Tableau des parties
    assert (
        "| Date | Couleur | Résultat | Cadence | ECO / Ouverture | Adversaire | Lien |"
        in opening_content
    )
    assert "Sicilian Defense" in opening_content
    assert "Opponent1" in opening_content
    assert "Opponent2" in opening_content

    # Section PGN
    assert "## PGN des parties" in opening_content
    assert "```pgn" in opening_content
    assert '[Event "Game1"]' in opening_content
    assert '[Event "Game2"]' in opening_content

    # 8) Message console
    captured = capsys.readouterr()
    assert "[chess→obsidian]" in captured.out
    assert "2 parties traitées" in captured.out
    assert "1 ouvertures" in captured.out
    assert str(obsidian_root) in captured.out


def test_build_parser_default_limit() -> None:
    """Le parser CLI doit avoir une valeur par défaut cohérente pour --limit."""
    parser = mod.build_parser()
    args = parser.parse_args([])
    assert args.limit == 200


def test_main_calls_sync_with_custom_limit(monkeypatch) -> None:
    """main() doit transmettre le --limit à sync_chess_to_obsidian."""
    called_with: list[int] = []

    def fake_sync(limit: int) -> None:
        called_with.append(limit)

    monkeypatch.setattr(mod, "sync_chess_to_obsidian", fake_sync)

    mod.main(["--limit", "42"])

    assert called_with == [42]
