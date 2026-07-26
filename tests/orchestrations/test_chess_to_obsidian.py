import datetime as dt
import hashlib
from dataclasses import replace

import pytest

from hanuman.models.chess import ChessGame, chess_game_path
from hanuman.models.chess_insight import ChessInsight, ChessInsightEnvelope
from hanuman.orchestrations import chess_to_obsidian as mod
from hanuman.services.chess_insight_storage_service import (
    inject_insight_block,
    parse_insight_block,
)


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


@pytest.mark.parametrize(
    "markdown",
    [
        f"{mod.ANALYSIS_START}\nseul",
        f"seul\n{mod.ANALYSIS_END}",
        f"{mod.ANALYSIS_START}\na\n{mod.ANALYSIS_START}\nb\n{mod.ANALYSIS_END}",
        f"{mod.ANALYSIS_END}\n{mod.ANALYSIS_START}",
    ],
)
def test_analysis_extraction_rejects_ambiguous_markers(markdown: str) -> None:
    with pytest.raises(mod.ChessGameNoteUpdateError, match="Marqueurs"):
        mod._extract_analysis(markdown)


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
        "games_protected": 0,
        "protected_game_files": [],
        "protected_game_diagnostics": [],
        "vault_games_usable": 2,
        "vault_notes_ignored": 0,
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


def test_sync_preserves_existing_structured_insights(tmp_path, monkeypatch) -> None:
    obsidian_root = tmp_path / "Echecs"
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(obsidian_root))
    monkeypatch.setattr(mod, "ChessService", FakeChessService)
    mod.sync_chess_to_obsidian(limit=1)
    path = obsidian_root / "2024" / "01" / "2024-01-02 - B20 - Opponent2.md"
    envelope = ChessInsightEnvelope(
        schema_version=1,
        game_id="g2",
        eco="B20",
        insights=(),
    )
    path.write_text(
        inject_insight_block(path.read_text(encoding="utf-8"), envelope),
        encoding="utf-8",
    )

    mod.sync_chess_to_obsidian(limit=1)

    assert parse_insight_block(path.read_text(encoding="utf-8")) == envelope


def test_sync_preserves_human_content_outside_generated_zones(tmp_path, monkeypatch) -> None:
    root = tmp_path / "Echecs"
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(root))
    monkeypatch.setattr(mod, "ChessService", FakeChessService)
    mod.sync_chess_to_obsidian(limit=1)
    path = root / "2024/01/2024-01-02 - B20 - Opponent2.md"
    content = path.read_text(encoding="utf-8")
    before_analysis = """## Notes personnelles

### Travail à revoir

- [[Lien humain]]
- Commentaire avec accents.
- Une ligne avant le bloc d’analyse.

"""
    after_insights = "\n- Une ligne après le bloc ChessInsight.\n"
    content = content.replace(mod.ANALYSIS_START, before_analysis + mod.ANALYSIS_START)
    content += after_insights
    path.write_text(content, encoding="utf-8")

    mod.sync_chess_to_obsidian(limit=1)

    updated = path.read_text(encoding="utf-8")
    assert before_analysis in updated
    assert updated.endswith(after_insights)


def test_sync_disambiguates_colliding_games_deterministically(tmp_path, monkeypatch) -> None:
    root = tmp_path / "Echecs"
    base = FakeChessService().get_latest_games("prakasch", 1)[0]
    first = {**base, "id": "collision-a", "pgn": '[Event "A"]\n\n1. e4 e5'}
    second = {**base, "id": "collision-b", "pgn": '[Event "B"]\n\n1. d4 d5'}

    class CollisionService:
        calls = 0

        def get_latest_games(self, username: str, limit: int) -> list[dict]:
            type(self).calls += 1
            return [second, first] if type(self).calls == 1 else [first, second]

    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(root))
    monkeypatch.setattr(mod, "ChessService", CollisionService)
    mod.sync_chess_to_obsidian(limit=2)
    first_state = {path.name: path.read_bytes() for path in sorted((root / "2024/01").glob("*.md"))}
    mod.sync_chess_to_obsidian(limit=2)
    second_state = {
        path.name: path.read_bytes() for path in sorted((root / "2024/01").glob("*.md"))
    }

    assert len(first_state) == 2
    suffix = hashlib.sha256(b"collision-b").hexdigest()[:8]
    assert any(f" - {suffix}.md" in name for name in first_state)
    assert b'[Event "A"]' in b"".join(first_state.values())
    assert b'[Event "B"]' in b"".join(first_state.values())
    assert second_state == first_state


@pytest.mark.parametrize("game_id", [None, "", "   "])
def test_select_game_paths_refuses_invalid_game_id_without_writing(
    tmp_path, game_id: str | None
) -> None:
    root = tmp_path / "Echecs"
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("intact", encoding="utf-8")
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    with pytest.raises(mod.ChessGameNoteUpdateError, match="Identifiant Chess vide"):
        mod._select_game_paths(
            root,
            [replace(_sample_game(), game_id=game_id)],  # type: ignore[arg-type]
        )

    assert not root.exists()
    assert {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before


def test_select_game_paths_refuses_real_suffix_collision_before_writing(tmp_path) -> None:
    root = tmp_path / "Echecs"
    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_text("intact", encoding="utf-8")
    sample = _sample_game()
    games = [
        replace(sample, game_id="!", pgn='[Event "base"]'),
        replace(sample, game_id="collision-55045", pgn='[Event "first"]'),
        replace(sample, game_id="collision-70885", pgn='[Event "second"]'),
    ]
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    with pytest.raises(mod.ChessGameNoteUpdateError, match="Collision de destination"):
        mod._select_game_paths(root, games)

    assert {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before
    assert not root.exists()
    assert hashlib.sha256(b"collision-55045").hexdigest()[:8] == "45560c60"
    assert hashlib.sha256(b"collision-70885").hexdigest()[:8] == "45560c60"


def test_sync_refuses_symbolic_chess_root_before_writing(tmp_path, monkeypatch) -> None:
    real_root = tmp_path / "real"
    symbolic_root = tmp_path / "symbolic"
    real_root.mkdir()
    symbolic_root.symlink_to(real_root, target_is_directory=True)
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(symbolic_root))
    monkeypatch.setattr(mod, "ChessService", FakeChessService)

    with pytest.raises(ValueError, match="Racine Chess symbolique"):
        mod.sync_chess_to_obsidian(limit=1)

    assert list(real_root.iterdir()) == []


def test_select_game_paths_accepts_identical_duplicate_identity_in_any_order(tmp_path) -> None:
    root = tmp_path / "Echecs"
    game = _sample_game()

    first = mod._select_game_paths(root, [game, game])
    second = mod._select_game_paths(root, [game, game][::-1])

    assert first == second
    assert len(first.games) == 1
    assert first.protected_notes == ()


def test_select_game_paths_refuses_contradictory_duplicate_identity(tmp_path) -> None:
    game = _sample_game()

    with pytest.raises(mod.ChessGameNoteUpdateError, match="Identité Chess contradictoire"):
        mod._select_game_paths(
            tmp_path / "Echecs",
            [
                game,
                replace(
                    game,
                    black="Autre adversaire",
                    eco="C20",
                    pgn='[Event "contradictoire"]',
                ),
            ],
        )


def test_historical_identity_has_three_distinct_states() -> None:
    valid = mod._historical_identity('---\ngame_id: "g1"\n---\n')
    absent = mod._historical_identity("---\ntype: chess-game\n---\n")
    invalid = mod._historical_identity('---\ngame_id: "g1"\n')

    assert valid == mod.HistoricalChessIdentity("valid", game_id="g1")
    assert absent == mod.HistoricalChessIdentity("absent")
    assert invalid.state == "invalid"
    assert invalid.reason == "Frontmatter Chess incomplet."


@pytest.mark.parametrize(
    ("ambiguous_content", "reason"),
    [
        ("Note humaine sans frontmatter.\n", "Frontmatter Chess absent ou invalide."),
        ('---\ngame_id: "g1"\n', "Frontmatter Chess incomplet."),
    ],
)
@pytest.mark.parametrize("reverse", [False, True])
def test_sync_protects_invalid_historical_identity_without_duplicate(
    tmp_path,
    monkeypatch,
    ambiguous_content: str,
    reason: str,
    reverse: bool,
) -> None:
    root = tmp_path / "Echecs"
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(root))
    monkeypatch.setattr(mod, "ChessService", FakeChessService)
    mod.sync_chess_to_obsidian(limit=2)
    protected = root / "2024/01/2024-01-01 - B20 - Opponent1.md"
    safe = root / "2024/01/2024-01-02 - B20 - Opponent2.md"
    protected.write_text(ambiguous_content, encoding="utf-8")
    protected_before = protected.read_bytes()
    safe_before = safe.read_bytes()
    received = FakeChessService().get_latest_games("prakasch", 2)

    class OrderedService:
        def get_latest_games(self, username: str, limit: int) -> list[dict]:
            return list(reversed(received)) if reverse else received

    monkeypatch.setattr(mod, "ChessService", OrderedService)
    result = mod.sync_chess_to_obsidian(limit=2)

    assert protected.read_bytes() == protected_before
    assert safe.read_bytes() == safe_before
    assert result["games_written"] == 1
    assert result["games_protected"] == 1
    assert result["protected_game_files"] == ["2024/01/2024-01-01 - B20 - Opponent1.md"]
    assert result["protected_game_diagnostics"] == [
        {
            "path": "2024/01/2024-01-01 - B20 - Opponent1.md",
            "reason": reason,
        }
    ]
    assert sorted(path.name for path in (root / "2024/01").glob("*.md")) == [
        "2024-01-01 - B20 - Opponent1.md",
        "2024-01-02 - B20 - Opponent2.md",
    ]


def test_updated_game_note_refreshes_owned_frontmatter_and_preserves_human_bytes() -> None:
    game = _sample_game()
    analysis = (
        f"{mod.ANALYSIS_START}\n## Analyse Stockfish\n\n"
        "### Ton bilan\n\nAnalyse terminée.\n"
        f"{mod.ANALYSIS_END}"
    )
    existing = mod._game_note(game, analysis)
    existing = existing.replace(
        "game_id: \"g1\"\n",
        'game_id: "g1"\nhuman_key: "Échec personnalisé"\n',
    )
    existing = existing.replace(
        "tags:\n",
        "tags:\n  - humain/premier\n  - échec-humain\n",
    )
    suffix = "\n## Notes humaines\n\nTexte Unicode conservé.\n"
    existing += suffix
    updated_game = replace(
        game,
        result="loss",
        eco="C20",
        url="https://chess.com/game/corrected",
        black="Nouvel adversaire",
    )

    updated = mod._updated_game_note(existing, updated_game)

    assert updated is not None
    assert "result: loss\n" in updated
    assert "eco: C20\n" in updated
    assert 'opponent: "Nouvel adversaire"\n' in updated
    assert 'chess_url: "https://chess.com/game/corrected"\n' in updated
    assert "analysis_status: analysed\n" in updated
    assert "  - chess/analysis/analysed\n" in updated
    assert "  - humain/premier\n  - échec-humain\n" in updated
    assert 'human_key: "Échec personnalisé"\n' in updated
    assert analysis in updated
    assert updated.endswith(suffix)
    assert mod._updated_game_note(updated, updated_game) == updated


@pytest.mark.parametrize(
    "existing",
    [
        "sans frontmatter",
        "---\ntype: chess-game\n",
        "---\ntype: chess-game\ntype: duplicate\n---\n",
        "---\ntype: chess-game # commentaire\n---\n",
    ],
)
def test_updated_game_note_refuses_ambiguous_frontmatter(existing: str) -> None:
    marked = f"{existing}\n{mod.GAME_START}\ncontenu\n{mod.GAME_END}\n"

    with pytest.raises(mod.ChessGameNoteUpdateError, match="Frontmatter|frontmatter|Commentaire"):
        mod._updated_game_note(marked, _sample_game())


def test_sync_protects_historical_note_without_game_markers(tmp_path, monkeypatch) -> None:
    root = tmp_path / "Echecs"
    path = root / "2024/01/2024-01-02 - B20 - Opponent2.md"
    path.parent.mkdir(parents=True)
    historical = """---
type: chess-game
game_id: "g2"
color: black
eco: B20
---

## Notes personnelles

Intouchable.
"""
    path.write_text(historical, encoding="utf-8")
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(root))
    monkeypatch.setattr(mod, "ChessService", FakeChessService)

    result = mod.sync_chess_to_obsidian(limit=1)

    assert path.read_text(encoding="utf-8") == historical
    assert result["games_protected"] == 1
    assert result["protected_game_files"] == [str(path.relative_to(root))]
    assert result["protected_game_diagnostics"] == [
        {
            "path": str(path.relative_to(root)),
            "reason": "Zone de partie Hanuman absente ; migration sûre requise.",
        }
    ]


@pytest.mark.parametrize("reverse", [False, True])
def test_sync_isolates_ambiguous_note_and_writes_safe_games(
    tmp_path, monkeypatch, reverse: bool
) -> None:
    root = tmp_path / "Echecs"
    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(root))
    monkeypatch.setattr(mod, "ChessService", FakeChessService)
    mod.sync_chess_to_obsidian(limit=2)
    ambiguous = root / "2024/01/2024-01-01 - B20 - Opponent1.md"
    safe_existing = root / "2024/01/2024-01-02 - B20 - Opponent2.md"
    ambiguous.write_text(
        ambiguous.read_text(encoding="utf-8").replace(
            "tags:\n",
            "tags: {chess/game: true, humain: true}\n",
        ),
        encoding="utf-8",
    )
    ambiguous_before = ambiguous.read_bytes()
    safe_before = safe_existing.read_bytes()
    games = FakeChessService().get_latest_games("prakasch", 2)
    third = {
        **games[0],
        "id": "g3",
        "end_time": games[1]["end_time"] + dt.timedelta(days=1),
        "black": "Opponent3",
        "url": "https://chess.com/game/3",
        "pgn": '[Event "Game3"]\n\n1. d4 d5',
    }
    received = [*games, third]

    class MixedService:
        def get_latest_games(self, username: str, limit: int) -> list[dict]:
            return list(reversed(received)) if reverse else received

    monkeypatch.setattr(mod, "ChessService", MixedService)
    result = mod.sync_chess_to_obsidian(limit=3)
    new_note = root / "2024/01/2024-01-03 - B20 - Opponent3.md"

    assert ambiguous.read_bytes() == ambiguous_before
    assert safe_existing.read_bytes() == safe_before
    assert new_note.is_file()
    assert result["games_written"] == 2
    assert result["games_protected"] == 1
    assert result["protected_game_files"] == ["2024/01/2024-01-01 - B20 - Opponent1.md"]
    assert result["protected_game_diagnostics"] == [
        {
            "path": "2024/01/2024-01-01 - B20 - Opponent1.md",
            "reason": "Format de tags non pris en charge dans de note Chess.",
        }
    ]


def test_limited_sync_rebuilds_views_from_complete_vault(tmp_path, monkeypatch) -> None:
    root = tmp_path / "Echecs"
    old_games: list[ChessGame] = []
    for index in range(3, 9):
        game = ChessGame(
            game_id=f"old-{index}",
            end_time=dt.datetime(2024, 1, index, 12, tzinfo=dt.timezone.utc),
            white="prakasch",
            black=f"OldOpponent{index}",
            result="win",
            color="white",
            opening_name="Sicilian Defense",
            eco="B20",
            time_control="blitz",
            url=f"https://example.test/{index}",
            pgn=f'[Event "Old {index}"]\n\n1. e4 c5',
        )
        old_games.append(game)
        path = chess_game_path(root, game)
        path.parent.mkdir(parents=True, exist_ok=True)
        note = mod._game_note(game)
        if index <= 7:
            insight = ChessInsight(
                insight_id=f"{game.game_id}:1:blunder:player",
                game_id=game.game_id,
                category="blunder",
                subtype="opening",
                ply=1,
                move_number=1,
                color="white",
                san="e4",
                annotation="??",
                fen_before=None,
                fen_after=None,
                eval_before_cp=100,
                eval_after_cp=-100,
                loss_cp=200,
                best_move_san="d4",
                principal_variation=("d4",),
                opening_phase=True,
                eco="B20",
                player_role="player",
            )
            note = inject_insight_block(
                note,
                ChessInsightEnvelope(1, game.game_id, "B20", (insight,)),
            )
        path.write_text(note, encoding="utf-8")
    before = {
        chess_game_path(root, game): chess_game_path(root, game).read_bytes() for game in old_games
    }

    monkeypatch.setenv("CHESS_OBSIDIAN_PATH", str(root))
    monkeypatch.setattr(mod, "ChessService", FakeChessService)
    result = mod.sync_chess_to_obsidian(limit=2)

    dashboard = (root / "_Index/Dashboard.md").read_text(encoding="utf-8")
    summary = root / "_Index/Gaffes/En ouverture.md"
    assert result["games_received"] == 2
    assert result["vault_games_usable"] == 8
    assert "**8 parties**" in dashboard
    assert "Synthèse durable" in summary.read_text(encoding="utf-8")
    assert {path: path.read_bytes() for path in before} == before


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
