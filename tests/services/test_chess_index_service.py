import datetime as dt
from dataclasses import replace
from pathlib import Path

import pytest

from hanuman.models.chess import ChessGame, chess_game_path
from hanuman.models.chess_insight import ChessInsight, ChessInsightEnvelope
from hanuman.services.chess_analysis_summary_service import (
    ANALYSIS_END,
    ANALYSIS_START,
)
from hanuman.services.chess_index_service import write_chess_indexes
from hanuman.services.chess_insight_storage_service import (
    INSIGHTS_END,
    INSIGHTS_START,
    inject_insight_block,
)


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


def _analysed_note(
    *,
    blunders: int = 2,
    mistakes: int = 3,
    dubious: int = 4,
    excellent: int = 5,
    missed: int = 6,
    average_loss: float = 42.5,
) -> str:
    return f"""# Partie

{ANALYSIS_START}
## Analyse Stockfish

### Ton bilan

- **Moteur :** Stockfish 17
- **Profondeur :** 18
- **Perte moyenne :** {average_loss} cp par coup joué
- **Pire coup :** 12.Dxe4??
- **Moment de bascule :** 12.Dxe4??

| Qualité | Nombre |
|---|---:|
| `??` Gaffes | {blunders} |
| `?` Erreurs | {mistakes} |
| `?!` Coups douteux | {dubious} |
| `!!` Excellents coups | {excellent} |
| Excellents coups manqués | {missed} |
{ANALYSIS_END}
"""


def test_write_chess_indexes_generates_adr_views(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"

    written = write_chess_indexes(root, _games())

    assert written == 7
    expected_paths = {
        Path("_Index/Dashboard.md"),
        Path("_Index/Profil échiquéen.md"),
        Path("_Index/Ouvertures/B20.md"),
        Path("_Index/Motifs/Index.md"),
        Path("_Index/Gaffes/Index.md"),
        Path("_Index/Excellents coups/Index.md"),
        Path("_Index/Opportunités/Index.md"),
    }
    assert set(_markdown_files(root)) == expected_paths
    assert not (root / "Dashboard.md").exists()
    assert not (root / "_Index/Annees").exists()
    assert not (root / "_Index/Mois").exists()
    assert not (root / "_Index/Adversaires").exists()

    dashboard = (root / "_Index/Dashboard.md").read_text(encoding="utf-8")
    assert dashboard.startswith("---\ntype: chess-dashboard\ncssclasses:\n")
    assert "  - hanuman-chess-dashboard\n" in dashboard
    assert "# ♛ Tableau de bord Échecs" in dashboard
    assert "> [!chess] Bibliothèque Caïssa" in dashboard
    assert "> **2 parties** · **1 ouvertures** · **2 adversaires**  " in dashboard
    assert "> 🟢 1 victoires · 🟡 0 nulles · 🔴 1 défaites" in dashboard
    assert "**0 parties analysées sur 2**" in dashboard
    assert "🟡 2 en attente · ⚠️ 0 illisibles" in dashboard
    assert "`??` 0 gaffes · `!!` 0 excellents coups" in dashboard
    assert "[[Echecs/_Index/Profil échiquéen|Profil échiquéen]]" in dashboard
    assert "[[Echecs/_Index/Ouvertures/B20|B20]]" in dashboard
    assert "[[Echecs/_Index/Motifs/Index|Motifs]]" in dashboard
    assert "[[Echecs/_Index/Gaffes/Index|Gaffes]]" in dashboard
    assert "[[Echecs/_Index/Excellents coups/Index|Excellents coups]]" in dashboard
    assert "[[Echecs/_Index/Opportunités/Index|Opportunités]]" in dashboard
    assert "_Index/Annees" not in dashboard
    assert "_Index/Mois" not in dashboard
    assert "_Index/Adversaires" not in dashboard
    assert dashboard.index("2024-01-02 · B20") < dashboard.index("2024-01-01 · B20")

    opening = (root / "_Index/Ouvertures/B20.md").read_text(encoding="utf-8")
    assert "type: chess-index" in opening
    assert "  - hanuman-index-opening" in opening
    assert "index_kind: opening" in opening
    assert 'index_key: "B20"' in opening
    assert "# B20 — Sicilian Defense" in opening
    assert "> [!chess] Vue d’ensemble" in opening
    assert "> 🏠 [[Echecs/_Index/Dashboard|Retour au tableau de bord]]" in opening
    assert opening.index("2024-01-02 · B20") < opening.index("2024-01-01 · B20")

    profile = (root / "_Index/Profil échiquéen.md").read_text(encoding="utf-8")
    assert "type: chess-profile" in profile
    assert "  - hanuman-chess-profile" in profile
    assert "# 👤 Profil échiquéen" in profile
    assert "**2 parties** · 🟢 1 victoires · 🟡 0 nulles · 🔴 1 défaites" in profile
    assert "⚪ 1 avec les Blancs · ⚫ 1 avec les Noirs" in profile
    assert "## Cadences principales\n\n**blitz** (2)" in profile
    assert "## Ouvertures principales\n\n" "**[[Echecs/_Index/Ouvertures/B20|B20]]** (2)" in profile
    assert "<!-- HANUMAN:GENERATED:START -->" in profile
    assert "<!-- HANUMAN:GENERATED:END -->" in profile
    assert "## Notes personnelles" in profile
    assert "## Analyse Stockfish globale" in profile
    assert "**0 parties analysées sur 2** · **0.0 %** de couverture" in profile
    assert "🟡 2 en attente · ⚠️ 0 illisibles" in profile
    assert "**Perte moyenne globale :** indisponible" in profile

    for directory in ("Motifs", "Gaffes", "Excellents coups", "Opportunités"):
        content = (root / "_Index" / directory / "Index.md").read_text(encoding="utf-8")
        assert f"# {directory}" in content
        assert "[[Echecs/_Index/Dashboard|Retour au tableau de bord]]" in content
        if directory == "Motifs":
            assert "Aucun détecteur de motifs échiquéens" in content
        else:
            assert "Groupes calculés exclusivement depuis les blocs ChessInsight" in content


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


def test_write_chess_indexes_preserves_legacy_files(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    legacy_files = {
        root / "_Index/Annees/2024.md": "Index annuel historique",
        root / "_Index/Mois/2024-01.md": "Index mensuel historique",
        root / "_Index/Adversaires/Opponent1.md": "Index adversaire historique",
    }
    for path, content in legacy_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    write_chess_indexes(root, _games())

    for path, content in legacy_files.items():
        assert path.read_text(encoding="utf-8") == content


def test_write_chess_indexes_preserves_profile_personal_notes(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    write_chess_indexes(root, _games())
    profile = root / "_Index/Profil échiquéen.md"
    personal_notes = """## Notes personnelles

### Priorités à revoir

- Travailler mes finales de tours.
- Revoir [[Echecs/_Index/Ouvertures/B20|la Sicilienne]].

Éviter les décisions précipitées avec les pièces légères.
"""
    annotated = (
        profile.read_text(encoding="utf-8").split("## Notes personnelles", 1)[0] + personal_notes
    )
    profile.write_text(annotated, encoding="utf-8")
    before_personal = profile.read_text(encoding="utf-8").split("## Notes personnelles", 1)[1]

    write_chess_indexes(root, _games()[:1])
    write_chess_indexes(root, _games()[:1])

    updated = profile.read_text(encoding="utf-8")
    after_personal = updated.split("## Notes personnelles", 1)[1]
    assert "**1 parties**" in updated
    assert after_personal == before_personal


def test_write_chess_indexes_aggregates_existing_notes_without_modifying_them(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Echecs"
    games = _games()
    analysed_path = chess_game_path(root, games[0])
    unreadable_path = chess_game_path(root, games[1])
    analysed_path.parent.mkdir(parents=True)
    analysed_path.write_text(_analysed_note(), encoding="utf-8")
    unreadable_path.write_text(
        f"{ANALYSIS_START}\n### Ton bilan\nbloc incomplet\n{ANALYSIS_END}",
        encoding="utf-8",
    )
    before = {
        analysed_path: analysed_path.read_bytes(),
        unreadable_path: unreadable_path.read_bytes(),
    }

    write_chess_indexes(root, games)

    profile = (root / "_Index/Profil échiquéen.md").read_text(encoding="utf-8")
    dashboard = (root / "_Index/Dashboard.md").read_text(encoding="utf-8")
    assert "**1 parties analysées sur 2** · **50.0 %** de couverture" in profile
    assert "🟡 0 en attente · ⚠️ 1 illisibles" in profile
    assert "| `??` Gaffes | 2 | 2.00 |" in profile
    assert "| `?` Erreurs | 3 | 3.00 |" in profile
    assert "| `?!` Coups douteux | 4 | 4.00 |" in profile
    assert "| `!!` Excellents coups | 5 | 5.00 |" in profile
    assert "| Excellents coups manqués | 6 | 6.00 |" in profile
    assert "**Perte moyenne globale :** 42.5 cp par coup joué" in profile
    assert "**1 parties analysées sur 2**" in dashboard
    assert "`??` 2 gaffes · `!!` 5 excellents coups" in dashboard
    assert {path: path.read_bytes() for path in before} == before
    assert list(root.glob("_Index/Gaffes/*.md")) == [root / "_Index/Gaffes/Index.md"]
    assert list(root.glob("_Index/Motifs/*.md")) == [root / "_Index/Motifs/Index.md"]


def test_write_chess_indexes_does_not_overwrite_unmarked_profile(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Echecs"
    profile = root / "_Index/Profil échiquéen.md"
    profile.parent.mkdir(parents=True)
    profile.write_text("Profil entièrement humain", encoding="utf-8")

    written = write_chess_indexes(root, _games())

    assert written == 6
    assert profile.read_text(encoding="utf-8") == "Profil entièrement humain"


def test_dashboard_and_opening_human_files_are_protected(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    dashboard = root / "_Index/Dashboard.md"
    opening = root / "_Index/Ouvertures/B20.md"
    opening.parent.mkdir(parents=True)
    dashboard.write_text("Dashboard entièrement humain", encoding="utf-8")
    opening.write_text("Ouverture entièrement humaine", encoding="utf-8")

    written = write_chess_indexes(root, _games())

    assert written == 5
    assert dashboard.read_text(encoding="utf-8") == "Dashboard entièrement humain"
    assert opening.read_text(encoding="utf-8") == "Ouverture entièrement humaine"


def test_dashboard_and_opening_preserve_personal_notes(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    write_chess_indexes(root, _games())
    targets = [
        root / "_Index/Dashboard.md",
        root / "_Index/Ouvertures/B20.md",
    ]
    notes = "\n### Annotation humaine\n\n- [[Lien humain]] avec accents.\n"
    for path in targets:
        path.write_text(path.read_text(encoding="utf-8") + notes, encoding="utf-8")

    write_chess_indexes(root, _games()[:1])
    first = {path: path.read_bytes() for path in targets}
    write_chess_indexes(root, _games()[:1])

    assert {path: path.read_bytes() for path in targets} == first
    assert all(path.read_text(encoding="utf-8").endswith(notes) for path in targets)


def test_global_validation_failure_changes_no_existing_view(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    write_chess_indexes(root, _games())
    invalid = root / "_Index/Opportunités/Index.md"
    invalid.write_text(
        "<!-- HANUMAN:GENERATED:START -->\nzone incomplète",
        encoding="utf-8",
    )
    before = {path: path.read_bytes() for path in sorted((root / "_Index").rglob("*.md"))}

    with pytest.raises(ValueError, match="Marqueurs|marqueurs|invalide"):
        write_chess_indexes(root, _games()[:1])

    assert {path: path.read_bytes() for path in before} == before


def _structured_insight(
    game_id: str,
    suffix: str,
    category: str,
    subtype: str,
    ply: int,
) -> ChessInsight:
    return ChessInsight(
        insight_id=f"{game_id}:{suffix}",
        game_id=game_id,
        category=category,  # type: ignore[arg-type]
        subtype=subtype,
        ply=ply,
        move_number=(ply + 1) // 2,
        color="white",
        san=f"Move{ply}",
        annotation=None,
        fen_before=None,
        fen_after=None,
        eval_before_cp=100,
        eval_after_cp=-100,
        loss_cp=200,
        best_move_san="e4",
        principal_variation=("e4", "e5"),
        opening_phase=subtype == "opening",
        eco="B20",
        player_role="player",
    )


def test_write_chess_indexes_integrates_thresholds_without_touching_sources(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Echecs"
    template = _games()[0]
    games = [
        replace(
            template,
            game_id=f"g{index}",
            end_time=dt.datetime(2024, 1, index, 12, tzinfo=dt.timezone.utc),
            black=f"Opponent{index}",
        )
        for index in range(1, 8)
    ]
    for index, game in enumerate(games[:5], start=1):
        insights = [
            _structured_insight(game.game_id, "blunder-open", "blunder", "opening", 1),
            _structured_insight(
                game.game_id,
                "opportunity",
                "opportunity",
                "missed_excellent",
                3,
            ),
        ]
        if index <= 4:
            insights.append(
                _structured_insight(
                    game.game_id,
                    "blunder-late",
                    "blunder",
                    "middlegame_or_endgame",
                    20,
                )
            )
        if index <= 3:
            insights.append(
                _structured_insight(
                    game.game_id,
                    "excellent-open",
                    "excellent",
                    "opening",
                    5,
                )
            )
        if index <= 2:
            insights.append(
                _structured_insight(
                    game.game_id,
                    "excellent-late",
                    "excellent",
                    "middlegame_or_endgame",
                    30,
                )
            )
        if index == 1:
            insights.extend(
                [
                    _structured_insight(
                        game.game_id,
                        "blunder-open-extra",
                        "blunder",
                        "opening",
                        7,
                    ),
                    insights[0],
                ]
            )
        path = chess_game_path(root, game)
        path.parent.mkdir(parents=True, exist_ok=True)
        envelope = ChessInsightEnvelope(1, game.game_id, game.eco, tuple(insights))
        path.write_text(
            inject_insight_block(
                "<!-- HANUMAN_CHESS_ANALYSIS_START -->\n"
                "Analyse visible intacte\n"
                "<!-- HANUMAN_CHESS_ANALYSIS_END -->\n",
                envelope,
            ),
            encoding="utf-8",
        )

    absent_path = chess_game_path(root, games[5])
    absent_path.write_text("Ancienne note sans insights", encoding="utf-8")
    invalid_path = chess_game_path(root, games[6])
    invalid_path.write_text(
        f"{INSIGHTS_START}\n```json\n{{invalid\n```\n{INSIGHTS_END}",
        encoding="utf-8",
    )
    human_summary = root / "_Index/Excellents coups/En ouverture.md"
    human_summary.parent.mkdir(parents=True, exist_ok=True)
    human_summary.write_text("Synthèse humaine préservée", encoding="utf-8")
    legacy = root / "_Index/Annees/2024.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("Legacy intact", encoding="utf-8")
    source_bytes = {
        chess_game_path(root, game): chess_game_path(root, game).read_bytes() for game in games
    }

    written = write_chess_indexes(root, games)
    blunder = root / "_Index/Gaffes/En ouverture.md"
    opportunity = root / "_Index/Opportunités/Excellents coups manqués.md"
    blunder_content = blunder.read_text(encoding="utf-8")
    annotated = blunder_content.replace(
        "Cette section sera préservée lors des prochaines générations.",
        "Annotation durable avec [[un lien]].",
    )
    blunder.write_text(annotated, encoding="utf-8")
    write_chess_indexes(root, games)
    first_views = {
        path.relative_to(root): path.read_bytes()
        for path in sorted((root / "_Index").rglob("*.md"))
    }
    write_chess_indexes(root, list(reversed(games)))
    second_views = {
        path.relative_to(root): path.read_bytes()
        for path in sorted((root / "_Index").rglob("*.md"))
    }

    assert written == 9
    assert blunder.is_file()
    assert opportunity.is_file()
    assert not (root / "_Index/Gaffes/Milieu de jeu ou finale.md").exists()
    assert not (root / "_Index/Excellents coups/Milieu de jeu ou finale.md").exists()
    assert list((root / "_Index/Motifs").glob("*.md")) == [root / "_Index/Motifs/Index.md"]
    assert "Synthèse durable" in blunder.read_text(encoding="utf-8")
    assert "6 occurrences" in blunder.read_text(encoding="utf-8")
    assert "Tendances confirmées" in (root / "_Index/Gaffes/Index.md").read_text(encoding="utf-8")
    assert "Signaux émergents" in (root / "_Index/Excellents coups/Index.md").read_text(
        encoding="utf-8"
    )
    assert "Couverture : 5/7 notes · 1 sans bloc · 1 illisibles" in (
        root / "_Index/Gaffes/Index.md"
    ).read_text(encoding="utf-8")
    assert human_summary.read_text(encoding="utf-8") == "Synthèse humaine préservée"
    assert "Annotation durable avec [[un lien]]." in blunder.read_text(encoding="utf-8")
    assert legacy.read_text(encoding="utf-8") == "Legacy intact"
    assert {path: path.read_bytes() for path in source_bytes} == source_bytes
    assert second_views == first_views
