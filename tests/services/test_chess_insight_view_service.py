from pathlib import Path

import pytest

from hanuman.models.chess_insight import ChessInsight
from hanuman.services.chess_insight_aggregation_service import (
    STATUS_CONFIRMED,
    STATUS_DURABLE,
    STATUS_EMERGING,
    ChessInsightAggregation,
    ChessInsightDiagnostics,
    ChessInsightGroup,
    ChessInsightOccurrence,
)
from hanuman.services.chess_insight_view_service import (
    GENERATED_END,
    GENERATED_START,
    INSIGHT_VIEW_DEFINITIONS,
    ChessInsightViewError,
    write_chess_insight_views,
)


def _occurrence(game: int, ply: int = 1) -> ChessInsightOccurrence:
    insight = ChessInsight(
        insight_id=f"g{game}:{ply}:blunder:player",
        game_id=f"g{game}",
        category="blunder",
        subtype="opening",
        ply=ply,
        move_number=(ply + 1) // 2,
        color="white",
        san=f"Move{ply}",
        annotation="??",
        fen_before=None,
        fen_after=None,
        eval_before_cp=100,
        eval_after_cp=-100,
        loss_cp=200,
        best_move_san="e4",
        principal_variation=("e4", "e5"),
        opening_phase=True,
        eco="B20",
        player_role="player",
    )
    return ChessInsightOccurrence(
        insight=insight,
        game_id=f"g{game}",
        note_path=Path(f"/vault/Echecs/2024/01/game-{game}.md"),
        note_link=f"[[Echecs/2024/01/game-{game}|Partie {game}]]",
        game_date=f"2024-01-{game:02d}",
        opponent=f"Opponent{game}",
        result="win",
        color="white",
    )


def _aggregation(
    count: int,
    status: str | None,
    *,
    extra_occurrence: bool = False,
) -> ChessInsightAggregation:
    occurrences = [_occurrence(game) for game in range(count, 0, -1)]
    if extra_occurrence and occurrences:
        occurrences.insert(1, _occurrence(count, ply=3))
    group = ChessInsightGroup(
        category="blunder",
        subtype="opening",
        occurrences=tuple(occurrences),
        occurrence_count=len(occurrences),
        unique_game_count=count,
        status=status,  # type: ignore[arg-type]
    )
    return ChessInsightAggregation(
        groups=(group,),
        diagnostics=ChessInsightDiagnostics(
            notes_total=count + 2,
            blocks_valid=count,
            blocks_absent=1,
            blocks_invalid=1,
            versions_unknown=0,
            duplicates_ignored=0,
            unsupported_insights_ignored=0,
        ),
    )


def test_controlled_french_filenames_are_safe() -> None:
    assert {item.filename for item in INSIGHT_VIEW_DEFINITIONS} == {
        "En ouverture.md",
        "Milieu de jeu ou finale.md",
        "Excellents coups manqués.md",
    }
    assert all(
        "/" not in item.filename and ".." not in item.filename and item.filename.strip()
        for item in INSIGHT_VIEW_DEFINITIONS
    )


@pytest.mark.parametrize(
    ("count", "status", "heading"),
    [
        (3, STATUS_EMERGING, "## Signaux émergents"),
        (4, STATUS_CONFIRMED, "## Tendances confirmées"),
    ],
)
def test_emerging_and_confirmed_stay_in_category_index(
    tmp_path: Path,
    count: int,
    status: str,
    heading: str,
) -> None:
    root = tmp_path / "Echecs"

    write_chess_insight_views(root, _aggregation(count, status))

    index = (root / "_Index/Gaffes/Index.md").read_text(encoding="utf-8")
    assert heading in index
    assert f"{count} parties uniques · {count} occurrences" in index
    assert f"**{status}**" in index
    assert not (root / "_Index/Gaffes/En ouverture.md").exists()
    assert "[[Echecs/_Index/Gaffes/En ouverture|" not in index


def test_group_below_three_is_not_an_active_tendency(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"

    write_chess_insight_views(root, _aggregation(2, None))

    index = (root / "_Index/Gaffes/Index.md").read_text(encoding="utf-8")
    assert "**En ouverture**" not in index
    assert not (root / "_Index/Gaffes/En ouverture.md").exists()


def test_durable_summary_contains_grouped_deterministic_examples(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Echecs"

    written = write_chess_insight_views(
        root,
        _aggregation(5, STATUS_DURABLE, extra_occurrence=True),
    )

    summary_path = root / "_Index/Gaffes/En ouverture.md"
    summary = summary_path.read_text(encoding="utf-8")
    index = (root / "_Index/Gaffes/Index.md").read_text(encoding="utf-8")
    assert written == 4
    assert "type: chess-insight-summary" in summary
    assert "# Gaffes — En ouverture" in summary
    assert "> [!chess] Synthèse durable" in summary
    assert "**5 parties uniques** · **6 occurrences**" in summary
    assert "Première occurrence enregistrée :** 2024-01-01" in summary
    assert "Dernière occurrence enregistrée :** 2024-01-05" in summary
    assert summary.count("### [[Echecs/2024/01/game-5|Partie 5]]") == 1
    assert summary.index("**1. Move1**") < summary.index("**2. Move3**")
    assert summary.index("Partie 5") < summary.index("Partie 4")
    assert "meilleur coup `e4`" in summary
    assert "ECO B20" in summary
    assert "[[Echecs/_Index/Gaffes/Index|Gaffes]]" in summary
    assert "[[Echecs/_Index/Dashboard|Tableau de bord]]" in summary
    assert "## Notes personnelles" in summary
    assert "[[Echecs/_Index/Gaffes/En ouverture|En ouverture]]" in index
    assert "Synthèses durables actives" in index


def test_generation_is_idempotent_and_preserves_personal_notes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Echecs"
    aggregation = _aggregation(5, STATUS_DURABLE)
    write_chess_insight_views(root, aggregation)
    summary_path = root / "_Index/Gaffes/En ouverture.md"
    personal = """## Notes personnelles

### Travail

- Revoir [[cette partie]].
- Garder les accents : échec.
"""
    content = summary_path.read_text(encoding="utf-8")
    summary_path.write_text(
        content.split("## Notes personnelles", 1)[0] + personal,
        encoding="utf-8",
    )

    write_chess_insight_views(root, aggregation)
    first = {path.relative_to(root): path.read_bytes() for path in sorted(root.rglob("*.md"))}
    write_chess_insight_views(root, aggregation)
    second = {path.relative_to(root): path.read_bytes() for path in sorted(root.rglob("*.md"))}

    assert second == first
    assert summary_path.read_text(encoding="utf-8").endswith(personal)


def test_regression_keeps_summary_and_marks_it_inactive(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    write_chess_insight_views(root, _aggregation(5, STATUS_DURABLE))
    summary_path = root / "_Index/Gaffes/En ouverture.md"
    before_paths = set(root.rglob("*.md"))

    write_chess_insight_views(root, _aggregation(2, None))

    summary = summary_path.read_text(encoding="utf-8")
    index = (root / "_Index/Gaffes/Index.md").read_text(encoding="utf-8")
    assert set(root.rglob("*.md")) == before_paths
    assert "Inactive — seuil actuellement non atteint" in summary
    assert "## Synthèses inactives" in index
    assert "[[Echecs/_Index/Gaffes/En ouverture|En ouverture]]" in index
    assert "**En ouverture**" not in index


def test_human_file_is_preserved_and_never_linked(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    path = root / "_Index/Gaffes/En ouverture.md"
    path.parent.mkdir(parents=True)
    path.write_text("Synthèse entièrement humaine", encoding="utf-8")

    write_chess_insight_views(root, _aggregation(5, STATUS_DURABLE))

    index = (root / "_Index/Gaffes/Index.md").read_text(encoding="utf-8")
    assert path.read_text(encoding="utf-8") == "Synthèse entièrement humaine"
    assert "[[Echecs/_Index/Gaffes/En ouverture|" not in index


def test_incomplete_generated_markers_are_refused(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    path = root / "_Index/Gaffes/Index.md"
    path.parent.mkdir(parents=True)
    path.write_text(f"{GENERATED_START}\ncontenu incomplet", encoding="utf-8")

    with pytest.raises(ChessInsightViewError, match="Marqueurs"):
        write_chess_insight_views(root, _aggregation(3, STATUS_EMERGING))


def test_no_individual_motif_note_is_ever_created(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"

    write_chess_insight_views(root, _aggregation(5, STATUS_DURABLE))

    assert not (root / "_Index/Motifs").exists()
    assert GENERATED_END in (root / "_Index/Gaffes/En ouverture.md").read_text(encoding="utf-8")
