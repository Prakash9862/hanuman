from pathlib import Path

from hanuman.services.chess_analysis_summary_service import (
    ANALYSIS_END,
    ANALYSIS_START,
    ChessAnalysisSummary,
    aggregate_analysis_summaries,
    parse_analysis_summary,
    read_analysis_summary,
)


def _analysis_block(
    *,
    engine: str = "Stockfish 17 évaluation",
    depth: str = "18",
    average_loss: str = "42.5",
    blunders: str = "2",
    mistakes: str = "3",
    dubious: str = "4",
    excellent: str = "5",
    missed: str = "6",
) -> str:
    return f"""# Note humaine

{ANALYSIS_START}
## Analyse Stockfish

### Ton bilan

- **Moteur :** {engine}
- **Profondeur :** {depth}
- **Perte moyenne :** {average_loss} cp par coup joué
- **Pire coup :** 18...Dxe4??
- **Moment de bascule :** 18...Dxe4??

| Qualité | Nombre |
|---|---:|
| `??` Gaffes | {blunders} |
| `?` Erreurs | {mistakes} |
| `?!` Coups douteux | {dubious} |
| `!!` Excellents coups | {excellent} |
| Excellents coups manqués | {missed} |
{ANALYSIS_END}

## Notes personnelles

Éviter cette erreur à l’avenir.
"""


def test_parse_complete_analysis_extracts_stable_values() -> None:
    summary = parse_analysis_summary(_analysis_block())

    assert summary == ChessAnalysisSummary(
        status="analysed",
        engine="Stockfish 17 évaluation",
        depth=18,
        average_loss_cp=42.5,
        blunders=2,
        mistakes=3,
        dubious=4,
        excellent=5,
        missed_excellent=6,
        worst_move="18...Dxe4??",
        turning_point="18...Dxe4??",
    )
    assert summary.analysed


def test_parse_accepts_decimal_comma_and_minor_spacing_variations() -> None:
    markdown = _analysis_block(average_loss="12,75").replace(
        "| `??` Gaffes | 2 |", " |  `??` Gaffes   |  2  | "
    )

    summary = parse_analysis_summary(markdown)

    assert summary.status == "analysed"
    assert summary.average_loss_cp == 12.75
    assert summary.blunders == 2


def test_parse_detects_pending_analysis() -> None:
    markdown = (
        f"{ANALYSIS_START}\n## Analyse Stockfish\n\n"
        "Analyse non encore lancée.\n"
        f"{ANALYSIS_END}"
    )

    assert parse_analysis_summary(markdown).status == "pending"


def test_parse_note_without_markers_is_pending_and_ignores_human_table() -> None:
    markdown = """# Notes personnelles

| Qualité | Nombre |
|---|---:|
| `??` Gaffes | 99 |
| `?` Erreurs | 99 |
| `?!` Coups douteux | 99 |
| `!!` Excellents coups | 99 |
| Excellents coups manqués | 99 |
"""

    summary = parse_analysis_summary(markdown)

    assert summary.status == "pending"
    assert summary.blunders == 0


def test_parse_ignores_analysis_like_content_outside_markers() -> None:
    markdown = _analysis_block(blunders="1") + "\n| `??` Gaffes | 88 |\n"

    assert parse_analysis_summary(markdown).blunders == 1


def test_parse_incomplete_block_is_unreadable() -> None:
    markdown = _analysis_block().replace("| `?` Erreurs | 3 |\n", "")

    assert parse_analysis_summary(markdown).status == "unreadable"


def test_parse_missing_optional_values_remains_explicit() -> None:
    markdown = _analysis_block()
    for line in (
        "- **Moteur :** Stockfish 17 évaluation\n",
        "- **Profondeur :** 18\n",
        "- **Perte moyenne :** 42.5 cp par coup joué\n",
        "- **Pire coup :** 18...Dxe4??\n",
        "- **Moment de bascule :** 18...Dxe4??\n",
    ):
        markdown = markdown.replace(line, "")

    summary = parse_analysis_summary(markdown)

    assert summary.status == "analysed"
    assert summary.engine is None
    assert summary.depth is None
    assert summary.average_loss_cp is None
    assert summary.worst_move is None
    assert summary.turning_point is None


def test_parse_malformed_content_never_raises() -> None:
    cases = [
        f"{ANALYSIS_START}\nbloc sans fin",
        f"bloc sans début\n{ANALYSIS_END}",
        _analysis_block(blunders="NaN"),
        "\x00\x00 texte arbitraire",
    ]

    assert [parse_analysis_summary(case).status for case in cases] == [
        "unreadable",
        "unreadable",
        "unreadable",
        "pending",
    ]


def test_read_missing_note_is_pending(tmp_path: Path) -> None:
    assert read_analysis_summary(tmp_path / "absente.md").status == "pending"


def test_aggregate_counts_only_valid_analyses_and_rounds_stably() -> None:
    summaries = [
        ChessAnalysisSummary(
            status="analysed",
            average_loss_cp=10.0,
            blunders=1,
            mistakes=2,
            dubious=3,
            excellent=4,
            missed_excellent=5,
        ),
        ChessAnalysisSummary(
            status="analysed",
            average_loss_cp=15.5,
            blunders=2,
            mistakes=3,
            dubious=4,
            excellent=5,
            missed_excellent=6,
        ),
        ChessAnalysisSummary(status="pending"),
        ChessAnalysisSummary(status="unreadable"),
    ]

    stats = aggregate_analysis_summaries(4, summaries)

    assert stats.games_analysed == 2
    assert stats.games_pending == 1
    assert stats.games_unreadable == 1
    assert stats.total_blunders == 3
    assert stats.total_mistakes == 5
    assert stats.total_dubious == 7
    assert stats.total_excellent == 9
    assert stats.total_missed_excellent == 11
    assert stats.average_blunders_per_analysed_game == 1.5
    assert stats.average_mistakes_per_analysed_game == 2.5
    assert stats.average_dubious_per_analysed_game == 3.5
    assert stats.average_excellent_per_analysed_game == 4.5
    assert stats.average_missed_excellent_per_analysed_game == 5.5
    assert stats.average_loss_cp == 12.8
    assert stats.analysis_coverage_percent == 50.0


def test_aggregate_pending_and_unreadable_are_not_zero_quality_games() -> None:
    stats = aggregate_analysis_summaries(
        3,
        [
            ChessAnalysisSummary(status="analysed", mistakes=3),
            ChessAnalysisSummary(status="pending", mistakes=200),
            ChessAnalysisSummary(status="unreadable", mistakes=300),
        ],
    )

    assert stats.total_mistakes == 3
    assert stats.average_mistakes_per_analysed_game == 3.0


def test_aggregate_handles_zero_games_and_missing_losses() -> None:
    stats = aggregate_analysis_summaries(0, [])

    assert stats.games_analysed == 0
    assert stats.average_blunders_per_analysed_game == 0.0
    assert stats.average_loss_cp is None
    assert stats.analysis_coverage_percent == 0.0


def test_aggregate_is_independent_of_summary_order() -> None:
    summaries = [
        ChessAnalysisSummary(status="analysed", blunders=1),
        ChessAnalysisSummary(status="analysed", blunders=2),
        ChessAnalysisSummary(status="pending"),
    ]

    assert aggregate_analysis_summaries(3, summaries) == aggregate_analysis_summaries(
        3, list(reversed(summaries))
    )
