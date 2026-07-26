from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Callable

from hanuman.models.chess import ChessGame
from hanuman.services.atomic_write_service import atomic_write_text

TitleFactory = Callable[[str, list[ChessGame]], str]


def _safe(value: str) -> str:
    value = re.sub(r"[^\w\-. ]+", "", value, flags=re.UNICODE).strip()
    return re.sub(r"\s+", " ", value) or "partie"


def _yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _filename(game: ChessGame) -> str:
    date = game.end_time.strftime("%Y-%m-%d")
    return f"{date} - {game.eco} - {_safe(game.opponent)}.md"


def _game_link(game: ChessGame) -> str:
    path = f"Echecs/{game.year}/{game.end_time.strftime('%m')}/{_filename(game)[:-3]}"
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
> 🏠 [[Dashboard|Retour au tableau de bord]]

## Parties

{links}
'''


def _dashboard(games: list[ChessGame]) -> str:
    years = sorted({game.year for game in games}, reverse=True)
    months = sorted({game.month for game in games}, reverse=True)
    openings = sorted({game.eco for game in games})
    opponents = sorted({_safe(game.opponent) for game in games}, key=str.lower)
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

## Navigation

> [!hanuman-nav] Années
> {' · '.join(f'[[_Index/Annees/{year}|{year}]]' for year in years)}

> [!hanuman-nav] Mois
> {' · '.join(f'[[_Index/Mois/{month}|{month}]]' for month in months)}

> [!hanuman-nav] Ouvertures
> {' · '.join(f'[[_Index/Ouvertures/{eco}|{eco}]]' for eco in openings)}

## Parties récentes

{recent}
'''


def write_chess_indexes(root: Path, games: list[ChessGame]) -> int:
    """Génère les vues Chess actuelles sans supprimer les fichiers existants."""

    index_root = root / "_Index"

    by_year: dict[str, list[ChessGame]] = defaultdict(list)
    by_month: dict[str, list[ChessGame]] = defaultdict(list)
    by_opening: dict[str, list[ChessGame]] = defaultdict(list)
    by_opponent: dict[str, list[ChessGame]] = defaultdict(list)

    for game in games:
        by_year[game.year].append(game)
        by_month[game.month].append(game)
        by_opening[game.eco].append(game)
        by_opponent[_safe(game.opponent)].append(game)

    written = 0
    groups: list[tuple[str, str, dict[str, list[ChessGame]], TitleFactory]] = [
        ("Annees", "year", by_year, lambda key, _: key),
        ("Mois", "month", by_month, lambda key, _: key),
        (
            "Ouvertures",
            "opening",
            by_opening,
            lambda key, grouped: f"{key} — {grouped[0].opening_name}",
        ),
        (
            "Adversaires",
            "opponent",
            by_opponent,
            lambda _, grouped: grouped[0].opponent,
        ),
    ]

    for directory, kind, grouped_values, title_factory in groups:
        target = index_root / directory
        target.mkdir(parents=True, exist_ok=True)
        for key, grouped_games in grouped_values.items():
            grouped_games.sort(key=lambda game: game.end_time, reverse=True)
            title = title_factory(key, grouped_games)
            atomic_write_text(
                target / f"{key}.md",
                _index_note(kind, key, title, grouped_games),
            )
            written += 1

    atomic_write_text(root / "Dashboard.md", _dashboard(games))
    return written + 1
