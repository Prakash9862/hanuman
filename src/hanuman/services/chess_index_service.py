from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from hanuman.models.chess import (
    ChessGame,
    chess_game_note_link,
    chess_game_path,
)
from hanuman.models.chess_insight import InsightCategory
from hanuman.services.chess_analysis_summary_service import (
    ChessProfileStats,
    build_chess_profile_stats,
    read_analysis_summary,
)
from hanuman.services.chess_insight_aggregation_service import (
    STATUS_CONFIRMED,
    STATUS_DURABLE,
    STATUS_EMERGING,
    ChessInsightAggregation,
    ChessInsightDiagnostics,
    ChessInsightGroup,
    aggregate_persisted_chess_insights,
)
from hanuman.services.chess_insight_view_service import plan_chess_insight_views_report
from hanuman.services.chess_view_write_plan_service import (
    ChessViewWritePlan,
    plan_generated_view,
)

GENERATED_START = "<!-- HANUMAN:GENERATED:START -->"
GENERATED_END = "<!-- HANUMAN:GENERATED:END -->"
THEMATIC_DIRECTORIES = ("Motifs",)
DASHBOARD_FRONTMATTER_KEYS = frozenset({"type", "cssclasses", "games_count", "tags"})
PROFILE_FRONTMATTER_KEYS = frozenset({"type", "cssclasses", "games_count", "tags"})
OPENING_FRONTMATTER_KEYS = frozenset(
    {"type", "cssclasses", "index_kind", "index_key", "games_count", "tags"}
)


@dataclass(frozen=True)
class ChessIndexWriteReport:
    general_views_written: int
    opening_indexes_written: int
    thematic_indexes_written: int
    active_summaries_written: int
    inactive_summaries_updated: int
    human_files_protected: int
    insight_diagnostics: ChessInsightDiagnostics

    @property
    def total_written(self) -> int:
        return (
            self.general_views_written
            + self.opening_indexes_written
            + self.thematic_indexes_written
            + self.active_summaries_written
            + self.inactive_summaries_updated
        )


def _yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _game_link(game: ChessGame) -> str:
    return chess_game_note_link(game)


def _index_note_generated(kind: str, key: str, title: str, games: list[ChessGame]) -> str:
    links = "\n".join(f"- {_game_link(game)}" for game in games)
    wins = sum(game.result == "win" for game in games)
    draws = sum(game.result == "draw" for game in games)
    losses = sum(game.result == "loss" for game in games)
    return f"""{GENERATED_START}
# {title}

> [!chess] Vue d’ensemble
> **{len(games)} parties** · 🟢 {wins} victoires · 🟡 {draws} nulles · 🔴 {losses} défaites{"  "}
> 🏠 [[Echecs/_Index/Dashboard|Retour au tableau de bord]]

## Parties

{links}
{GENERATED_END}"""


def _index_note(kind: str, key: str, title: str, games: list[ChessGame]) -> str:
    return f'''---
type: chess-index
cssclasses:
  - hanuman-chess
  - hanuman-chess-index
  - hanuman-index-{kind}
index_kind: {kind}
index_key: {_yaml_quote(key)}
games_count: {len(games)}
tags:
  - chess/index/{kind}
---

{_index_note_generated(kind, key, title, games)}

## Notes personnelles

Cette section sera préservée lors des prochaines générations.
'''


def _group_label(group: ChessInsightGroup) -> str:
    labels = {
        ("blunder", "opening"): "Gaffes — En ouverture",
        ("blunder", "middlegame_or_endgame"): "Gaffes — Milieu de jeu ou finale",
        ("excellent", "opening"): "Excellents coups — En ouverture",
        (
            "excellent",
            "middlegame_or_endgame",
        ): "Excellents coups — Milieu de jeu ou finale",
        ("opportunity", "missed_excellent"): "Opportunités — Excellents coups manqués",
    }
    return labels[(group.category, group.subtype)]


def _trend_lines(aggregation: ChessInsightAggregation, status: str) -> str:
    lines = [
        f"- **{_group_label(group)}** — {group.unique_game_count} parties uniques"
        for group in aggregation.groups
        if group.status == status
    ]
    return "\n".join(lines) or "Aucune."


def _existing_inactive_summaries(root: Path, aggregation: ChessInsightAggregation) -> list[str]:
    current = {(group.category, group.subtype): group for group in aggregation.groups}
    definitions: dict[tuple[InsightCategory, str], tuple[str, str, str]] = {
        ("blunder", "opening"): ("Gaffes", "En ouverture.md", "Gaffes — En ouverture"),
        (
            "blunder",
            "middlegame_or_endgame",
        ): ("Gaffes", "Milieu de jeu ou finale.md", "Gaffes — Milieu de jeu ou finale"),
        (
            "excellent",
            "opening",
        ): ("Excellents coups", "En ouverture.md", "Excellents coups — En ouverture"),
        (
            "excellent",
            "middlegame_or_endgame",
        ): (
            "Excellents coups",
            "Milieu de jeu ou finale.md",
            "Excellents coups — Milieu de jeu ou finale",
        ),
        (
            "opportunity",
            "missed_excellent",
        ): (
            "Opportunités",
            "Excellents coups manqués.md",
            "Opportunités — Excellents coups manqués",
        ),
    }
    inactive = []
    for key, (directory, filename, label) in definitions.items():
        path = root / "_Index" / directory / filename
        group = current.get(key)
        if path.is_file() and (group is None or group.status != STATUS_DURABLE):
            inactive.append(
                f"- [[Echecs/_Index/{directory}/{filename[:-3]}|{label}]] — "
                "Inactive — seuil actuellement non atteint"
            )
    return inactive


def _legacy_files(root: Path) -> list[Path]:
    candidates = [root / "Dashboard.md"]
    candidates.extend(
        sorted((root / "Openings").glob("*.md"))
        if (root / "Openings").is_dir() and not (root / "Openings").is_symlink()
        else []
    )
    for directory in ("Années", "Annees", "Mois", "Adversaires"):
        path = root / "_Index" / directory
        if path.is_dir() and not path.is_symlink():
            candidates.extend(sorted(path.rglob("*.md")))
    return [path for path in candidates if path.is_file()]


def _dashboard_generated(
    root: Path,
    games: list[ChessGame],
    stats: ChessProfileStats,
    aggregation: ChessInsightAggregation,
) -> str:
    openings = sorted({game.eco for game in games})
    analysed_games = [
        game for game in games if read_analysis_summary(chess_game_path(root, game)).analysed
    ]
    recent = "\n".join(f"- {_game_link(game)}" for game in analysed_games[:10]) or "Aucune."
    wins = sum(game.result == "win" for game in games)
    draws = sum(game.result == "draw" for game in games)
    losses = sum(game.result == "loss" for game in games)
    durable = _trend_lines(aggregation, STATUS_DURABLE)
    confirmed = _trend_lines(aggregation, STATUS_CONFIRMED)
    emerging = _trend_lines(aggregation, STATUS_EMERGING)
    inactive = _existing_inactive_summaries(root, aggregation)
    inactive_section = (
        "\n## Synthèses inactives\n\n" + "\n".join(inactive) + "\n" if inactive else ""
    )
    warnings = []
    if stats.games_unreadable:
        warnings.append(
            f"- **Statuts d’analyse contradictoires ou illisibles :** "
            f"{stats.games_unreadable} note(s)."
        )
    warnings.extend(
        f"- **Fichier legacy protégé :** `{path.relative_to(root)}`."
        for path in _legacy_files(root)
    )
    if aggregation.diagnostics.blocks_valid < 3:
        warnings.append(
            "- **Données insuffisantes :** moins de 3 notes possèdent des insights "
            "structurés exploitables."
        )
    warning_text = "\n".join(warnings) or "Aucun avertissement."
    opening_links = (
        " · ".join(f"[[Echecs/_Index/Ouvertures/{eco}|{eco}]]" for eco in openings)
        or "Données insuffisantes."
    )
    return f"""{GENERATED_START}
# ♛ Tableau de bord Échecs

> [!chess] Résumé global
> **{len(games)} parties**{"  "}
> 🟢 {wins} victoires · 🟡 {draws} nulles · 🔴 {losses} défaites
> 🔬 **{stats.games_analysed} parties analysées sur {stats.games_total}** · ⏳ {stats.games_pending} en attente · ⚠️ {stats.games_unreadable} illisibles
> `??` {stats.total_blunders} gaffes · `!!` {stats.total_excellent} excellents coups

## Accès directs

> [!hanuman-nav] Synthèses analytiques
> 👤 [[Echecs/_Index/Profil échiquéen|Profil échiquéen]]
> 🧩 [[Echecs/_Index/Motifs/Index|Motifs]] · 💥 [[Echecs/_Index/Gaffes/Index|Gaffes]] · ✨ [[Echecs/_Index/Excellents coups/Index|Excellents coups]] · 🎯 [[Echecs/_Index/Opportunités/Index|Opportunités]]

### Ouvertures

{opening_links}

## Tendances actives

### Signaux émergents

{emerging}

### Tendances confirmées

{confirmed}

### Synthèses durables actives

{durable}
{inactive_section}
## Dernières parties analysées

{recent}

## Avertissements de cohérence

> [!warning] Diagnostic
{chr(10).join(f"> {line}" for line in warning_text.splitlines())}
{GENERATED_END}"""


def _dashboard(
    root: Path,
    games: list[ChessGame],
    stats: ChessProfileStats,
    aggregation: ChessInsightAggregation,
) -> str:
    return f"""---
type: chess-dashboard
cssclasses:
  - hanuman-chess
  - hanuman-chess-dashboard
games_count: {len(games)}
tags:
  - chess/dashboard
---

{_dashboard_generated(root, games, stats, aggregation)}

## Notes personnelles

Cette section sera préservée lors des prochaines générations.
"""


def _ranked_counts(values: list[str]) -> str:
    counts = Counter(values)
    return (
        " · ".join(
            f"**{value}** ({count})"
            for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        )
        or "Aucune"
    )


def _result_line(games: list[ChessGame]) -> str:
    wins = sum(game.result == "win" for game in games)
    draws = sum(game.result == "draw" for game in games)
    losses = sum(game.result == "loss" for game in games)
    return f"{len(games)} parties · {wins} victoires · {draws} nulles · {losses} défaites"


def _opening_performance(games: list[ChessGame], *, best: bool) -> str:
    grouped: dict[str, list[ChessGame]] = defaultdict(list)
    for game in games:
        grouped[game.eco].append(game)
    if not grouped:
        return "Données insuffisantes."
    ranked = sorted(
        grouped.items(),
        key=lambda item: (
            sum(game.result == "win" for game in item[1]) / len(item[1]),
            len(item[1]),
            item[0],
        ),
        reverse=best,
    )
    eco, opening_games = ranked[0]
    return f"[[Echecs/_Index/Ouvertures/{eco}|{eco}]] — {_result_line(opening_games)}"


def _recurrences(aggregation: ChessInsightAggregation, category: str) -> str:
    groups = [
        group
        for group in aggregation.groups
        if group.category == category and group.unique_game_count >= 3
    ]
    if not groups:
        return "Données insuffisantes."
    return "\n".join(
        f"- **{_group_label(group)}** — {group.unique_game_count} parties uniques"
        for group in groups
    )


def _profile_generated(
    games: list[ChessGame],
    stats: ChessProfileStats,
    aggregation: ChessInsightAggregation,
) -> str:
    wins = sum(game.result == "win" for game in games)
    draws = sum(game.result == "draw" for game in games)
    losses = sum(game.result == "loss" for game in games)
    white_games = [game for game in games if game.color == "white"]
    black_games = [game for game in games if game.color == "black"]
    return f"""{GENERATED_START}
# 👤 Profil échiquéen

> [!chess] Vue d’ensemble
> **{len(games)} parties** · 🟢 {wins} victoires · 🟡 {draws} nulles · 🔴 {losses} défaites{"  "}
> **Avec les Blancs :** {_result_line(white_games)}{"  "}
> **Avec les Noirs :** {_result_line(black_games)}{"  "}
> **Analyse :** {stats.games_analysed} analysées · {stats.games_pending} en attente · {stats.games_unreadable} illisibles

> [!hanuman-nav] Navigation
> 🏠 [[Echecs/_Index/Dashboard|Retour au tableau de bord]]

## Cadences principales

{_ranked_counts([game.time_control for game in games])}

## Ouvertures principales

{_ranked_counts([f"[[Echecs/_Index/Ouvertures/{game.eco}|{game.eco}]]" for game in games])}

### Meilleurs résultats

{_opening_performance(games, best=True)}

### Pires résultats

{_opening_performance(games, best=False)}

## Motifs récurrents

Données insuffisantes : aucun détecteur de motifs déterministe n’est disponible.

## Gaffes récurrentes

{_recurrences(aggregation, "blunder")}

## Excellents coups récurrents

{_recurrences(aggregation, "excellent")}

## Opportunités manquées récurrentes

{_recurrences(aggregation, "opportunity")}

## Analyse Stockfish globale

> [!stockfish] Couverture de l’analyse
> **{stats.games_analysed} parties analysées sur {stats.games_total}** · **{stats.analysis_coverage_percent:.1f} %** de couverture{"  "}
> 🟡 {stats.games_pending} en attente · ⚠️ {stats.games_unreadable} illisibles

| Mesure | Total | Moyenne par partie analysée |
|---|---:|---:|
| `??` Gaffes | {stats.total_blunders} | {stats.average_blunders_per_analysed_game:.2f} |
| `?` Erreurs | {stats.total_mistakes} | {stats.average_mistakes_per_analysed_game:.2f} |
| `?!` Coups douteux | {stats.total_dubious} | {stats.average_dubious_per_analysed_game:.2f} |
| `!!` Excellents coups | {stats.total_excellent} | {stats.average_excellent_per_analysed_game:.2f} |
| Excellents coups manqués | {stats.total_missed_excellent} | {stats.average_missed_excellent_per_analysed_game:.2f} |

**Perte moyenne globale :** {_format_average_loss(stats.average_loss_cp)}
{GENERATED_END}"""


def _format_average_loss(value: float | None) -> str:
    return f"{value:.1f} cp par coup joué" if value is not None else "indisponible"


def _profile(
    games: list[ChessGame],
    stats: ChessProfileStats,
    aggregation: ChessInsightAggregation,
) -> str:
    return f"""---
type: chess-profile
cssclasses:
  - hanuman-chess
  - hanuman-chess-profile
games_count: {len(games)}
tags:
  - chess/profile
---

{_profile_generated(games, stats, aggregation)}

## Notes personnelles

Cette section sera préservée lors des prochaines générations.
"""


def _thematic_generated(title: str) -> str:
    return f"""{GENERATED_START}
# {title}

> [!chess] Synthèses récurrentes
> Données insuffisantes : aucun détecteur de motifs échiquéens déterministe n’est actuellement disponible.

> [!hanuman-nav] Navigation
> 🏠 [[Echecs/_Index/Dashboard|Retour au tableau de bord]]

## Synthèses durables actives

Aucune.

## Tendances confirmées

Aucune.

## Signaux émergents

Aucun.
{GENERATED_END}"""


def _thematic_index(title: str) -> str:
    return f"""---
type: chess-index
cssclasses:
  - hanuman-chess
  - hanuman-chess-index
  - hanuman-chess-thematic
index_kind: thematic
tags:
  - chess/index/thematic
---

{_thematic_generated(title)}

## Notes personnelles

Cette section sera préservée lors des prochaines générations.
"""


def write_chess_indexes_report(root: Path, games: list[ChessGame]) -> ChessIndexWriteReport:
    """Génère les vues ADR-0005 sans supprimer les fichiers existants."""

    games = sorted(games, key=lambda game: game.end_time, reverse=True)
    index_root = root / "_Index"
    stats = build_chess_profile_stats(root, games)
    insight_aggregation = aggregate_persisted_chess_insights(root, games)

    by_opening: dict[str, list[ChessGame]] = defaultdict(list)

    for game in games:
        by_opening[game.eco].append(game)

    opening_written = 0
    opening_root = index_root / "Ouvertures"
    plan = ChessViewWritePlan()
    protected = 0
    for eco, grouped_games in by_opening.items():
        grouped_games.sort(key=lambda game: game.end_time, reverse=True)
        title = f"{eco} — {grouped_games[0].opening_name}"
        planned = plan_generated_view(
            root,
            opening_root / f"{eco}.md",
            initial=_index_note("opening", eco, title, grouped_games),
            generated=_index_note_generated("opening", eco, title, grouped_games),
            start_marker=GENERATED_START,
            end_marker=GENERATED_END,
            owned_frontmatter_keys=OPENING_FRONTMATTER_KEYS,
        )
        plan = plan.merged(planned)
        opening_written += int(bool(planned.writes))
        protected += len(planned.protected_files)

    dashboard_plan = plan_generated_view(
        root,
        index_root / "Dashboard.md",
        initial=_dashboard(root, games, stats, insight_aggregation),
        generated=_dashboard_generated(root, games, stats, insight_aggregation),
        start_marker=GENERATED_START,
        end_marker=GENERATED_END,
        owned_frontmatter_keys=DASHBOARD_FRONTMATTER_KEYS,
    )
    plan = plan.merged(dashboard_plan)
    general_written = int(bool(dashboard_plan.writes))
    protected += len(dashboard_plan.protected_files)

    profile_plan = plan_generated_view(
        root,
        index_root / "Profil échiquéen.md",
        initial=_profile(games, stats, insight_aggregation),
        generated=_profile_generated(games, stats, insight_aggregation),
        start_marker=GENERATED_START,
        end_marker=GENERATED_END,
        owned_frontmatter_keys=PROFILE_FRONTMATTER_KEYS,
    )
    plan = plan.merged(profile_plan)
    general_written += int(bool(profile_plan.writes))
    protected += len(profile_plan.protected_files)

    thematic_written = 0
    for title in THEMATIC_DIRECTORIES:
        target = index_root / title / "Index.md"
        planned = plan_generated_view(
            root,
            target,
            initial=_thematic_index(title),
            generated=_thematic_generated(title),
            start_marker=GENERATED_START,
            end_marker=GENERATED_END,
        )
        plan = plan.merged(planned)
        thematic_written += int(bool(planned.writes))
        protected += len(planned.protected_files)

    insight_plan, insight_report = plan_chess_insight_views_report(root, insight_aggregation)
    plan = plan.merged(insight_plan)
    plan.execute()

    return ChessIndexWriteReport(
        general_views_written=general_written,
        opening_indexes_written=opening_written,
        thematic_indexes_written=(thematic_written + insight_report.thematic_indexes_written),
        active_summaries_written=insight_report.active_summaries_written,
        inactive_summaries_updated=insight_report.inactive_summaries_updated,
        human_files_protected=protected + insight_report.human_files_protected,
        insight_diagnostics=insight_aggregation.diagnostics,
    )


def write_chess_indexes(root: Path, games: list[ChessGame]) -> int:
    """Génère les vues ADR-0005 et retourne le nombre de fichiers écrits."""

    return write_chess_indexes_report(root, games).total_written
