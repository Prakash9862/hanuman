from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hanuman.services.chess_analysis_summary_service import read_analysis_summary
from hanuman.services.chess_index_service import write_chess_indexes_report
from hanuman.services.chess_vault_reader_service import read_chess_vault


@dataclass(frozen=True)
class ChessViewRebuildReport:
    notes_discovered: int
    notes_usable: int
    notes_ignored: int
    general_views_written: int
    opening_indexes_written: int
    thematic_indexes_written: int
    active_summaries_written: int
    inactive_summaries_updated: int
    insight_blocks_absent: int
    insight_blocks_invalid: int
    unknown_schema_versions: int
    duplicates_ignored: int
    human_files_protected: int
    legacy_files: tuple[str, ...]
    errors: tuple[str, ...]
    analyses_valid: int
    games_pending: int
    analyses_invalid: int
    analyses_orphaned: int

    @property
    def views_written(self) -> int:
        return (
            self.general_views_written
            + self.opening_indexes_written
            + self.thematic_indexes_written
            + self.active_summaries_written
            + self.inactive_summaries_updated
        )


def _legacy_files(root: Path) -> tuple[str, ...]:
    paths = [root / "Dashboard.md"]
    openings = root / "Openings"
    if openings.is_dir() and not openings.is_symlink():
        paths.extend(sorted(openings.glob("*.md")))
    for directory in ("Années", "Annees", "Mois", "Adversaires"):
        legacy_directory = root / "_Index" / directory
        if legacy_directory.is_dir() and not legacy_directory.is_symlink():
            paths.extend(sorted(legacy_directory.rglob("*.md")))
    return tuple(str(path.relative_to(root)) for path in paths if path.is_file())


def rebuild_chess_views(
    root: Path,
    *,
    include_openings: bool = True,
) -> ChessViewRebuildReport:
    read_result = read_chess_vault(root)
    source_before = {
        ignored.path: ignored.path.read_bytes() for ignored in read_result.ignored_notes
    }
    source_before.update(
        {
            path: path.read_bytes()
            for path in sorted(
                path
                for year in root.iterdir()
                if year.is_dir() and year.name.isdigit() and len(year.name) == 4
                for month in year.iterdir()
                if month.is_dir() and month.name.isdigit() and len(month.name) == 2
                for path in month.glob("*.md")
            )
        }
    )
    all_files_before = {path for path in root.rglob("*") if path.is_file()}

    summaries = [
        read_analysis_summary(
            root / game.year / game.end_time.strftime("%m") / game.note_filename
        )
        for game in read_result.games
    ]
    valid = sum(summary.status == "analysed" for summary in summaries)
    pending = sum(summary.status == "pending" for summary in summaries)
    invalid = sum(summary.status == "unreadable" for summary in summaries)
    orphaned = 0
    for ignored in read_result.ignored_notes:
        if read_analysis_summary(ignored.path).status == "analysed":
            orphaned += 1

    write_report = write_chess_indexes_report(
        root,
        list(read_result.games),
        include_openings=include_openings,
    )

    source_after = {path: path.read_bytes() for path in source_before}
    if source_after != source_before:
        raise RuntimeError("La reconstruction a modifié une note de partie.")
    all_files_after = {path for path in root.rglob("*") if path.is_file()}
    if not all_files_before.issubset(all_files_after):
        raise RuntimeError("La reconstruction a supprimé un fichier existant.")

    diagnostics = write_report.insight_diagnostics
    return ChessViewRebuildReport(
        notes_discovered=read_result.notes_discovered,
        notes_usable=read_result.notes_usable,
        notes_ignored=read_result.notes_ignored,
        general_views_written=write_report.general_views_written,
        opening_indexes_written=write_report.opening_indexes_written,
        thematic_indexes_written=write_report.thematic_indexes_written,
        active_summaries_written=write_report.active_summaries_written,
        inactive_summaries_updated=write_report.inactive_summaries_updated,
        insight_blocks_absent=diagnostics.blocks_absent,
        insight_blocks_invalid=diagnostics.blocks_invalid,
        unknown_schema_versions=diagnostics.versions_unknown,
        duplicates_ignored=diagnostics.duplicates_ignored,
        human_files_protected=write_report.human_files_protected,
        legacy_files=_legacy_files(root),
        errors=tuple(
            f"{item.path.relative_to(root)} : {item.reason}" for item in read_result.ignored_notes
        ),
        analyses_valid=valid,
        games_pending=pending,
        analyses_invalid=invalid,
        analyses_orphaned=orphaned,
    )


def refresh_chess_knowledge(root: Path) -> ChessViewRebuildReport:
    """Relit les notes persistées et reconstruit les vues, hors index ECO."""

    return rebuild_chess_views(root, include_openings=False)
