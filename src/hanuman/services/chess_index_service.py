from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from hanuman.models.chess import (
    ChessGame,
    chess_game_filename,
    safe_chess_filename_part,
)
from hanuman.services.atomic_write_service import atomic_write_text
from hanuman.services.chess_analysis_summary_service import (
    ChessProfileStats,
    build_chess_profile_stats,
)

GENERATED_START = "<!-- HANUMAN:GENERATED:START -->"
GENERATED_END = "<!-- HANUMAN:GENERATED:END -->"
THEMATIC_DIRECTORIES = ("Motifs", "Gaffes", "Excellents coups", "Opportunités")


def _yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _game_link(game: ChessGame) -> str:
    path = f"Echecs/{game.year}/{game.end_time.strftime('%m')}/" f"{chess_game_filename(game)[:-3]}"
    label = (
        f"{game.end_time.strftime('%Y-%m-%d')} · {game.eco} · " f"{game.opponent} · {game.result}"
    )
    return f"[[{path}|{label}]]"


def _index_note(kind: str, key: str, title: str, games: list[ChessGame]) -> str:
    links = "\n".join(f"- {_game_link(game)}" for game in games)
    wins = sum(game.result == "win" for game in games)
    draws = sum(game.result == "draw" for game in games)
    losses = sum(game.result == "loss" for game in games)
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

# {title}

> [!chess] Vue d’ensemble
> **{len(games)} parties** · 🟢 {wins} victoires · 🟡 {draws} nulles · 🔴 {losses} défaites  
> 🏠 [[Echecs/_Index/Dashboard|Retour au tableau de bord]]

## Parties

{links}
'''


def _dashboard(games: list[ChessGame], stats: ChessProfileStats) -> str:
    openings = sorted({game.eco for game in games})
    opponents = sorted({safe_chess_filename_part(game.opponent) for game in games}, key=str.lower)
    recent = "\n".join(f"- {_game_link(game)}" for game in games[:30])
    wins = sum(game.result == "win" for game in games)
    draws = sum(game.result == "draw" for game in games)
    losses = sum(game.result == "loss" for game in games)
    return f'''---
type: chess-dashboard
cssclasses:
  - hanuman-chess
  - hanuman-chess-dashboard
games_count: {len(games)}
tags:
  - chess/dashboard
---

# ♛ Tableau de bord Échecs

> [!chess] Bibliothèque Caïssa
> **{len(games)} parties** · **{len(openings)} ouvertures** · **{len(opponents)} adversaires**  
> 🟢 {wins} victoires · 🟡 {draws} nulles · 🔴 {losses} défaites

> [!stockfish] Couverture Stockfish
> **{stats.games_analysed} parties analysées sur {stats.games_total}** · 🟡 {stats.games_pending} en attente · ⚠️ {stats.games_unreadable} illisibles{"  "}
> `??` {stats.total_blunders} gaffes · `!!` {stats.total_excellent} excellents coups · 👤 [[Echecs/_Index/Profil échiquéen|Voir le profil détaillé]]

## Navigation

> [!hanuman-nav] Bibliothèque
> 👤 [[Echecs/_Index/Profil échiquéen|Profil échiquéen]] · ♟️ {' · '.join(f'[[Echecs/_Index/Ouvertures/{eco}|{eco}]]' for eco in openings)}
> 🧩 [[Echecs/_Index/Motifs/Index|Motifs]] · 💥 [[Echecs/_Index/Gaffes/Index|Gaffes]] · ✨ [[Echecs/_Index/Excellents coups/Index|Excellents coups]] · 🎯 [[Echecs/_Index/Opportunités/Index|Opportunités]]

## Parties récentes

{recent}
'''


def _ranked_counts(values: list[str]) -> str:
    counts = Counter(values)
    return (
        " · ".join(
            f"**{value}** ({count})"
            for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        )
        or "Aucune"
    )


def _profile_generated(games: list[ChessGame], stats: ChessProfileStats) -> str:
    wins = sum(game.result == "win" for game in games)
    draws = sum(game.result == "draw" for game in games)
    losses = sum(game.result == "loss" for game in games)
    whites = sum(game.color == "white" for game in games)
    blacks = sum(game.color == "black" for game in games)
    return f"""{GENERATED_START}
# 👤 Profil échiquéen

> [!chess] Vue d’ensemble
> **{len(games)} parties** · 🟢 {wins} victoires · 🟡 {draws} nulles · 🔴 {losses} défaites{"  "}
> ⚪ {whites} avec les Blancs · ⚫ {blacks} avec les Noirs

> [!hanuman-nav] Navigation
> 🏠 [[Echecs/_Index/Dashboard|Retour au tableau de bord]]

## Cadences principales

{_ranked_counts([game.time_control for game in games])}

## Ouvertures principales

{_ranked_counts([f"[[Echecs/_Index/Ouvertures/{game.eco}|{game.eco}]]" for game in games])}

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


def _profile(games: list[ChessGame], stats: ChessProfileStats) -> str:
    return f"""---
type: chess-profile
cssclasses:
  - hanuman-chess
  - hanuman-chess-profile
games_count: {len(games)}
tags:
  - chess/profile
---

{_profile_generated(games, stats)}

## Notes personnelles

Cette section sera préservée lors des prochaines générations.
"""


def _thematic_generated(title: str) -> str:
    return f"""{GENERATED_START}
# {title}

> [!chess] Synthèses récurrentes
> Les synthèses seront générées lorsqu’une récurrence aura été confirmée.

> [!hanuman-nav] Navigation
> 🏠 [[Echecs/_Index/Dashboard|Retour au tableau de bord]]
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


def _replace_generated(existing: str, generated: str) -> str | None:
    if GENERATED_START not in existing or GENERATED_END not in existing:
        return None
    before, rest = existing.split(GENERATED_START, 1)
    _, after = rest.split(GENERATED_END, 1)
    return before + generated + after


def _write_protected(path: Path, initial: str, generated: str) -> bool:
    if not path.exists():
        atomic_write_text(path, initial)
        return True
    updated = _replace_generated(path.read_text(encoding="utf-8"), generated)
    if updated is None:
        return False
    atomic_write_text(path, updated)
    return True


def write_chess_indexes(root: Path, games: list[ChessGame]) -> int:
    """Génère les vues ADR-0005 sans supprimer les fichiers existants."""

    index_root = root / "_Index"
    stats = build_chess_profile_stats(root, games)

    by_opening: dict[str, list[ChessGame]] = defaultdict(list)

    for game in games:
        by_opening[game.eco].append(game)

    written = 0
    opening_root = index_root / "Ouvertures"
    opening_root.mkdir(parents=True, exist_ok=True)
    for eco, grouped_games in by_opening.items():
        grouped_games.sort(key=lambda game: game.end_time, reverse=True)
        title = f"{eco} — {grouped_games[0].opening_name}"
        atomic_write_text(
            opening_root / f"{eco}.md",
            _index_note("opening", eco, title, grouped_games),
        )
        written += 1

    atomic_write_text(index_root / "Dashboard.md", _dashboard(games, stats))
    written += 1
    if _write_protected(
        index_root / "Profil échiquéen.md",
        _profile(games, stats),
        _profile_generated(games, stats),
    ):
        written += 1

    for title in THEMATIC_DIRECTORIES:
        target = index_root / title / "Index.md"
        if _write_protected(target, _thematic_index(title), _thematic_generated(title)):
            written += 1

    return written
