from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hanuman.models.chess_insight import InsightCategory
from hanuman.services.atomic_write_service import atomic_write_text
from hanuman.services.chess_insight_aggregation_service import (
    STATUS_CONFIRMED,
    STATUS_DURABLE,
    STATUS_EMERGING,
    STATUS_INACTIVE,
    ChessInsightAggregation,
    ChessInsightGroup,
    ChessInsightOccurrence,
)

GENERATED_START = "<!-- HANUMAN:GENERATED:START -->"
GENERATED_END = "<!-- HANUMAN:GENERATED:END -->"


class ChessInsightViewError(ValueError):
    """Signale une vue Hanuman dont les marqueurs sont invalides."""


@dataclass(frozen=True)
class ChessInsightViewWriteReport:
    thematic_indexes_written: int
    active_summaries_written: int
    inactive_summaries_updated: int
    human_files_protected: int

    @property
    def total_written(self) -> int:
        return (
            self.thematic_indexes_written
            + self.active_summaries_written
            + self.inactive_summaries_updated
        )


@dataclass(frozen=True)
class InsightViewDefinition:
    category: InsightCategory
    subtype: str
    directory: str
    category_title: str
    title: str
    filename: str
    description: str

    @property
    def summary_path_parts(self) -> tuple[str, str]:
        return self.directory, self.filename


INSIGHT_VIEW_DEFINITIONS: tuple[InsightViewDefinition, ...] = (
    InsightViewDefinition(
        "blunder",
        "opening",
        "Gaffes",
        "Gaffes",
        "En ouverture",
        "En ouverture.md",
        "Gaffes enregistrées pendant la phase d’ouverture.",
    ),
    InsightViewDefinition(
        "blunder",
        "middlegame_or_endgame",
        "Gaffes",
        "Gaffes",
        "Milieu de jeu ou finale",
        "Milieu de jeu ou finale.md",
        "Gaffes enregistrées après la phase d’ouverture.",
    ),
    InsightViewDefinition(
        "excellent",
        "opening",
        "Excellents coups",
        "Excellents coups",
        "En ouverture",
        "En ouverture.md",
        "Excellents coups enregistrés pendant la phase d’ouverture.",
    ),
    InsightViewDefinition(
        "excellent",
        "middlegame_or_endgame",
        "Excellents coups",
        "Excellents coups",
        "Milieu de jeu ou finale",
        "Milieu de jeu ou finale.md",
        "Excellents coups enregistrés après la phase d’ouverture.",
    ),
    InsightViewDefinition(
        "opportunity",
        "missed_excellent",
        "Opportunités",
        "Opportunités",
        "Excellents coups manqués",
        "Excellents coups manqués.md",
        "Opportunités de jouer un excellent coup enregistrées comme manquées.",
    ),
)


def _replace_generated(existing: str, generated: str) -> str | None:
    starts = existing.count(GENERATED_START)
    ends = existing.count(GENERATED_END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise ChessInsightViewError("Marqueurs de vue Hanuman incomplets ou dupliqués.")
    start = existing.index(GENERATED_START)
    end = existing.index(GENERATED_END)
    if end < start:
        raise ChessInsightViewError("Marqueurs de vue Hanuman dans un ordre invalide.")
    return existing[:start] + generated + existing[end + len(GENERATED_END) :]


def _write_protected(path: Path, initial: str, generated: str) -> bool:
    if not path.exists():
        atomic_write_text(path, initial)
        return True
    updated = _replace_generated(path.read_text(encoding="utf-8"), generated)
    if updated is None:
        return False
    atomic_write_text(path, updated)
    return True


def _has_hanuman_markers(path: Path) -> bool:
    if not path.is_file():
        return False
    content = path.read_text(encoding="utf-8")
    starts = content.count(GENERATED_START)
    ends = content.count(GENERATED_END)
    if starts == 0 and ends == 0:
        return False
    if starts != 1 or ends != 1:
        raise ChessInsightViewError(f"Marqueurs de vue Hanuman invalides : {path}")
    return True


def _summary_link(definition: InsightViewDefinition) -> str:
    stem = definition.filename[:-3]
    return f"[[Echecs/_Index/{definition.directory}/{stem}|" f"{definition.title}]]"


def _index_entry(
    definition: InsightViewDefinition,
    group: ChessInsightGroup,
    *,
    link: bool,
    status: str,
) -> str:
    title = _summary_link(definition) if link else f"**{definition.title}**"
    return (
        f"- {title} — **{status}** · {group.unique_game_count} parties uniques · "
        f"{group.occurrence_count} occurrences"
    )


def _thematic_index_generated(
    definition: InsightViewDefinition,
    category_groups: list[ChessInsightGroup],
    active_links: set[tuple[InsightCategory, str]],
    inactive_links: set[tuple[InsightCategory, str]],
    diagnostics_text: str,
) -> str:
    durable: list[str] = []
    confirmed: list[str] = []
    emerging: list[str] = []
    inactive: list[str] = []
    definitions = {
        (item.category, item.subtype): item
        for item in INSIGHT_VIEW_DEFINITIONS
        if item.category == definition.category
    }
    for group in category_groups:
        key = (group.category, group.subtype)
        item = definitions[key]
        if key in inactive_links:
            inactive.append(_index_entry(item, group, link=True, status=STATUS_INACTIVE))
        elif group.status == STATUS_DURABLE:
            durable.append(
                _index_entry(
                    item,
                    group,
                    link=key in active_links,
                    status=STATUS_DURABLE,
                )
            )
        elif group.status == STATUS_CONFIRMED:
            confirmed.append(_index_entry(item, group, link=False, status=STATUS_CONFIRMED))
        elif group.status == STATUS_EMERGING:
            emerging.append(_index_entry(item, group, link=False, status=STATUS_EMERGING))

    sections = [
        "## Synthèses durables actives\n\n" + ("\n".join(durable) if durable else "Aucune."),
        "## Tendances confirmées\n\n" + ("\n".join(confirmed) if confirmed else "Aucune."),
        "## Signaux émergents\n\n" + ("\n".join(emerging) if emerging else "Aucun."),
    ]
    if inactive:
        sections.append("## Synthèses inactives\n\n" + "\n".join(inactive))

    return f"""{GENERATED_START}
# {definition.category_title}

> [!chess] Synthèses structurées
> Groupes calculés exclusivement depuis les blocs ChessInsight persistés.
> {diagnostics_text}

> [!hanuman-nav] Navigation
> 🏠 [[Echecs/_Index/Dashboard|Retour au tableau de bord]]

{chr(10).join(sections)}
{GENERATED_END}"""


def _thematic_index_initial(
    definition: InsightViewDefinition,
    generated: str,
) -> str:
    return f"""---
type: chess-index
cssclasses:
  - hanuman-chess
  - hanuman-chess-index
  - hanuman-chess-thematic
index_kind: thematic
category: {definition.category}
tags:
  - chess/index/thematic
---

{generated}

## Notes personnelles

Cette section sera préservée lors des prochaines générations.
"""


def _occurrence_line(occurrence: ChessInsightOccurrence) -> str:
    insight = occurrence.insight
    details = [f"**{insight.move_number}. {insight.san}**"]
    details.append(f"ply {insight.ply}")
    details.append(f"perte {insight.loss_cp} cp")
    if insight.best_move_san:
        details.append(f"meilleur coup `{insight.best_move_san}`")
    if insight.eco:
        details.append(f"ECO {insight.eco}")
    return "- " + " · ".join(details)


def _examples(group: ChessInsightGroup) -> str:
    by_game: dict[str, list[ChessInsightOccurrence]] = {}
    game_order: list[str] = []
    for occurrence in group.occurrences:
        if occurrence.game_id not in by_game:
            by_game[occurrence.game_id] = []
            game_order.append(occurrence.game_id)
        by_game[occurrence.game_id].append(occurrence)

    sections: list[str] = []
    for game_id in game_order:
        occurrences = by_game[game_id]
        first = occurrences[0]
        heading = first.note_link
        metadata = [
            value
            for value in (
                first.game_date,
                first.opponent,
                first.color,
                first.result,
            )
            if value
        ]
        sections.append(f"### {heading}")
        if metadata:
            sections.append("\n" + " · ".join(metadata))
        sections.append("\n" + "\n".join(_occurrence_line(item) for item in occurrences))
    return "\n\n".join(sections) if sections else "Aucune occurrence actuelle."


def _summary_generated(
    definition: InsightViewDefinition,
    group: ChessInsightGroup,
    status: str,
) -> str:
    dates = [
        occurrence.game_date for occurrence in group.occurrences if occurrence.game_date is not None
    ]
    first_date = min(dates) if dates else "indisponible"
    last_date = max(dates) if dates else "indisponible"
    return f"""{GENERATED_START}
# {definition.category_title} — {definition.title}

> [!chess] {status}
> **Catégorie :** {definition.category_title} · **Sous-type :** {definition.title}
> **{group.unique_game_count} parties uniques** · **{group.occurrence_count} occurrences**

{definition.description}

- **Première occurrence enregistrée :** {first_date}
- **Dernière occurrence enregistrée :** {last_date}

> [!hanuman-nav] Navigation
> 🗂️ [[Echecs/_Index/{definition.directory}/Index|{definition.category_title}]] · 🏠 [[Echecs/_Index/Dashboard|Tableau de bord]]

## Parties concernées

{_examples(group)}
{GENERATED_END}"""


def _empty_group(definition: InsightViewDefinition) -> ChessInsightGroup:
    return ChessInsightGroup(
        category=definition.category,
        subtype=definition.subtype,
        occurrences=(),
        occurrence_count=0,
        unique_game_count=0,
        status=None,
    )


def _summary_initial(
    definition: InsightViewDefinition,
    generated: str,
) -> str:
    return f"""---
type: chess-insight-summary
cssclasses:
  - hanuman-chess
  - hanuman-chess-index
  - hanuman-chess-insight-summary
category: {definition.category}
subtype: {definition.subtype}
tags:
  - chess/insight/{definition.category}
---

{generated}

## Notes personnelles

Cette section sera préservée lors des prochaines générations.
"""


def write_chess_insight_views_report(
    root: Path,
    aggregation: ChessInsightAggregation,
) -> ChessInsightViewWriteReport:
    index_root = root / "_Index"
    groups = {(group.category, group.subtype): group for group in aggregation.groups}
    active_links: set[tuple[InsightCategory, str]] = set()
    inactive_links: set[tuple[InsightCategory, str]] = set()
    active_written = 0
    inactive_written = 0
    protected = 0

    for definition in INSIGHT_VIEW_DEFINITIONS:
        key = (definition.category, definition.subtype)
        group = groups.get(key, _empty_group(definition))
        path = index_root / definition.directory / definition.filename
        existing_hanuman = _has_hanuman_markers(path)
        if group.status == STATUS_DURABLE:
            generated = _summary_generated(definition, group, STATUS_DURABLE)
            if _write_protected(
                path,
                _summary_initial(definition, generated),
                generated,
            ):
                active_links.add(key)
                active_written += 1
            else:
                protected += 1
        elif existing_hanuman:
            generated = _summary_generated(definition, group, STATUS_INACTIVE)
            if _write_protected(
                path,
                _summary_initial(definition, generated),
                generated,
            ):
                inactive_links.add(key)
                inactive_written += 1

    diagnostics = aggregation.diagnostics
    diagnostics_text = (
        f"Couverture : {diagnostics.blocks_valid}/{diagnostics.notes_total} notes · "
        f"{diagnostics.blocks_absent} sans bloc · "
        f"{diagnostics.blocks_invalid + diagnostics.versions_unknown} illisibles."
    )
    categories: tuple[InsightCategory, ...] = (
        "blunder",
        "excellent",
        "opportunity",
    )
    thematic_written = 0
    for category in categories:
        definitions = [item for item in INSIGHT_VIEW_DEFINITIONS if item.category == category]
        representative = definitions[0]
        category_groups = [
            groups.get((item.category, item.subtype), _empty_group(item)) for item in definitions
        ]
        generated = _thematic_index_generated(
            representative,
            category_groups,
            active_links,
            inactive_links,
            diagnostics_text,
        )
        path = index_root / representative.directory / "Index.md"
        if _write_protected(
            path,
            _thematic_index_initial(representative, generated),
            generated,
        ):
            thematic_written += 1
        else:
            protected += 1

    return ChessInsightViewWriteReport(
        thematic_indexes_written=thematic_written,
        active_summaries_written=active_written,
        inactive_summaries_updated=inactive_written,
        human_files_protected=protected,
    )


def write_chess_insight_views(
    root: Path,
    aggregation: ChessInsightAggregation,
) -> int:
    return write_chess_insight_views_report(root, aggregation).total_written
