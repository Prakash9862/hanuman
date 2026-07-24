from __future__ import annotations

import argparse
import datetime as dt
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hanuman.services.core.chess_service import ChessService

CHESS_USERNAME = "prakasch"
OBSIDIAN_ROOT = Path("/home/vince/Prakash/projets/Obsidian_Priv-/Echecs")


@dataclass(frozen=True)
class ChessGame:
    game_id: str
    end_time: dt.datetime
    white: str
    black: str
    result: str
    color: str
    opening_name: str
    eco: str
    time_control: str
    url: str
    pgn: str

    @property
    def opponent(self) -> str:
        return self.black if self.color == "white" else self.white


def _safe(value: str) -> str:
    value = re.sub(r"[^\w\-. ]+", "", value, flags=re.UNICODE).strip()
    return re.sub(r"\s+", " ", value) or "partie"


def _game_from_raw(raw: dict[str, Any]) -> ChessGame:
    return ChessGame(
        game_id=str(raw["id"]),
        end_time=raw["end_time"],
        white=str(raw["white"]),
        black=str(raw["black"]),
        result=str(raw["result"]),
        color=str(raw["color"]),
        opening_name=str(raw.get("opening_name") or "Ouverture inconnue"),
        eco=str(raw.get("eco") or "UNK").upper(),
        time_control=str(raw.get("time_control") or "inconnue"),
        url=str(raw.get("url") or ""),
        pgn=str(raw.get("pgn") or ""),
    )


def _game_note(game: ChessGame) -> str:
    date = game.end_time.strftime("%Y-%m-%d")
    opening_link = f"[[Openings/{game.eco[0] if game.eco != 'UNK' else 'Autres'}/{game.eco} - {_safe(game.opening_name)}]]"
    return f'''---
type: chess-game
date: {date}
platform: chess.com
username: {CHESS_USERNAME}
result: {game.result}
color: {game.color}
opponent: "{game.opponent}"
eco: {game.eco}
opening: "{game.opening_name}"
time_control: {game.time_control}
tags:
  - chess/game
  - chess/{game.result}
  - chess/{game.time_control}
  - eco/{game.eco}
---

# {game.white} vs {game.black}

## Résumé

- **Résultat :** {game.result}
- **Couleur :** {game.color}
- **Adversaire :** {game.opponent}
- **Cadence :** {game.time_control}
- **Ouverture :** {opening_link}
- **Chess.com :** [ouvrir la partie]({game.url})

## PGN

```pgn
{game.pgn.strip()}
```

## Analyse personnelle

### Moment critique

### Erreurs

### Ce que je dois retenir
'''


def _opening_note(eco: str, name: str, games: list[ChessGame]) -> str:
    wins = sum(g.result == "win" for g in games)
    draws = sum(g.result == "draw" for g in games)
    losses = sum(g.result == "loss" for g in games)
    score = round((wins + draws / 2) / len(games) * 100, 1) if games else 0
    links = []
    for game in sorted(games, key=lambda item: item.end_time, reverse=True):
        date = game.end_time.strftime("%Y-%m-%d")
        filename = f"{date} - {game.eco} - {_safe(game.white)} vs {_safe(game.black)}"
        links.append(f"- [[Parties/{game.end_time.year}/{filename}|{date} · {game.opponent} · {game.result}]]")
    return f'''---
type: chess-opening
eco: {eco}
opening: "{name}"
games_count: {len(games)}
tags:
  - chess/opening
  - eco/{eco}
---

# {eco} — {name}

## Statistiques personnelles

- **Parties :** {len(games)}
- **Victoires :** {wins}
- **Nulles :** {draws}
- **Défaites :** {losses}
- **Score :** {score} %

## Parties

{chr(10).join(links)}

## Notes personnelles

### Plans principaux

### Erreurs récurrentes

### Variantes à travailler
'''


def _dashboard(games: list[ChessGame], openings: dict[tuple[str, str], list[ChessGame]]) -> str:
    wins = sum(g.result == "win" for g in games)
    draws = sum(g.result == "draw" for g in games)
    losses = sum(g.result == "loss" for g in games)
    rows = []
    for (eco, name), grouped in sorted(openings.items(), key=lambda item: (-len(item[1]), item[0][0])):
        letter = eco[0] if eco != "UNK" else "Autres"
        rows.append(f"| [[Openings/{letter}/{eco} - {_safe(name)}|{eco} · {name}]] | {len(grouped)} |")
    return f'''---
title: "Chess.com → Obsidian"
username: {CHESS_USERNAME}
games_count: {len(games)}
openings_count: {len(openings)}
tags:
  - chess/dashboard
---

# Tableau de bord — {CHESS_USERNAME}

- **Parties importées :** {len(games)}
- **Victoires :** {wins}
- **Nulles :** {draws}
- **Défaites :** {losses}
- **Profil :** [Chess.com](https://www.chess.com/member/{CHESS_USERNAME})

## Ouvertures

| ECO / Ouverture | Parties |
|---|---:|
{chr(10).join(rows)}
'''


def sync_chess_to_obsidian(limit: int = 200) -> dict[str, Any]:
    raw_games = ChessService().get_latest_games(username=CHESS_USERNAME, limit=limit)
    games = [_game_from_raw(raw) for raw in raw_games]
    parties_root = OBSIDIAN_ROOT / "Parties"
    openings_root = OBSIDIAN_ROOT / "Openings"
    parties_root.mkdir(parents=True, exist_ok=True)
    openings_root.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    grouped: dict[tuple[str, str], list[ChessGame]] = defaultdict(list)

    for game in games:
        grouped[(game.eco, game.opening_name)].append(game)
        year_dir = parties_root / str(game.end_time.year)
        year_dir.mkdir(parents=True, exist_ok=True)
        date = game.end_time.strftime("%Y-%m-%d")
        filename = f"{date} - {game.eco} - {_safe(game.white)} vs {_safe(game.black)}.md"
        path = year_dir / filename
        if path.exists():
            skipped += 1
            continue
        path.write_text(_game_note(game), encoding="utf-8")
        created += 1

    for (eco, name), opening_games in grouped.items():
        letter = eco[0] if eco != "UNK" else "Autres"
        directory = openings_root / letter
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{eco} - {_safe(name)}.md").write_text(
            _opening_note(eco, name, opening_games), encoding="utf-8"
        )

    (OBSIDIAN_ROOT / "Dashboard.md").write_text(_dashboard(games, grouped), encoding="utf-8")
    return {
        "status": "ok",
        "username": CHESS_USERNAME,
        "destination": str(OBSIDIAN_ROOT),
        "games_received": len(games),
        "games_created": created,
        "games_skipped": skipped,
        "openings_updated": len(grouped),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Synchronise Chess.com vers Obsidian")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args(argv)
    print(sync_chess_to_obsidian(limit=args.limit))


if __name__ == "__main__":
    main()
