from __future__ import annotations

import argparse
import datetime as dt
import io
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chess.pgn

from hanuman.services.core.chess_service import ChessService

CHESS_USERNAME = "prakasch"
ANALYSIS_START = "<!-- HANUMAN_CHESS_ANALYSIS_START -->"
ANALYSIS_END = "<!-- HANUMAN_CHESS_ANALYSIS_END -->"


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


def _chess_root() -> Path:
    configured = os.environ.get("CHESS_OBSIDIAN_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    vault = Path(
        os.environ.get(
            "OBSIDIAN_VAULT_PATH",
            "/home/vince/Prakash/projets/Obsidian_Priv-",
        )
    ).expanduser()
    return (vault / "Echecs").resolve()


def _safe(value: str) -> str:
    value = re.sub(r"[^\w\-. ]+", "", value, flags=re.UNICODE).strip()
    return re.sub(r"\s+", " ", value) or "partie"


def _yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


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


def _parse_headers(pgn: str) -> dict[str, str]:
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        return {}
    return {str(key): str(value) for key, value in game.headers.items()}


def _headers_table(headers: dict[str, str]) -> str:
    if not headers:
        return "Aucun en-tête PGN disponible."
    rows = ["| Champ | Valeur |", "|---|---|"]
    for key, value in headers.items():
        clean = value.replace("|", "\\|").replace("\n", " ")
        rows.append(f"| **{key}** | {clean} |")
    return "\n".join(rows)


def _filename(game: ChessGame) -> str:
    date = game.end_time.strftime("%Y-%m-%d")
    return f"{date} - {game.eco} - {_safe(game.opponent)}.md"


def _game_note(game: ChessGame) -> str:
    date = game.end_time.strftime("%Y-%m-%d")
    headers = _parse_headers(game.pgn)
    title = f"{date} — {game.eco} — {game.opponent}"
    opening = headers.get("Opening") or game.opening_name
    white_elo = headers.get("WhiteElo", "")
    black_elo = headers.get("BlackElo", "")
    termination = headers.get("Termination", "")

    return f'''---
type: chess-game
date: {date}
platform: chess.com
username: {CHESS_USERNAME}
game_id: {_yaml_quote(game.game_id)}
result: {game.result}
color: {game.color}
opponent: {_yaml_quote(game.opponent)}
white: {_yaml_quote(game.white)}
black: {_yaml_quote(game.black)}
white_elo: {_yaml_quote(white_elo)}
black_elo: {_yaml_quote(black_elo)}
eco: {game.eco}
opening: {_yaml_quote(opening)}
time_control: {_yaml_quote(game.time_control)}
termination: {_yaml_quote(termination)}
chess_url: {_yaml_quote(game.url)}
tags:
  - chess/game
  - chess/result/{game.result}
  - chess/color/{game.color}
  - chess/time/{_safe(game.time_control).replace(' ', '-').lower()}
  - chess/opening/{game.eco}
---

# {title}

## Résumé

- **Résultat :** {game.result}
- **Couleur :** {game.color}
- **Adversaire :** {game.opponent}
- **Blancs :** {game.white}{f' ({white_elo})' if white_elo else ''}
- **Noirs :** {game.black}{f' ({black_elo})' if black_elo else ''}
- **Cadence :** {game.time_control}
- **Ouverture :** {game.eco} — {opening}
- **Fin de partie :** {termination or 'non précisée'}
- **Chess.com :** [ouvrir la partie]({game.url})

## En-têtes PGN

{_headers_table(headers)}

## PGN complet

```pgn
{game.pgn.strip()}
```

{ANALYSIS_START}
## Analyse Stockfish

Analyse non encore lancée.
{ANALYSIS_END}
'''


def _reset_root(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for child in root.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def sync_chess_to_obsidian(limit: int = 200, reset: bool = False) -> dict[str, Any]:
    root = _chess_root()
    if reset:
        _reset_root(root)
    else:
        root.mkdir(parents=True, exist_ok=True)

    raw_games = ChessService().get_latest_games(username=CHESS_USERNAME, limit=limit)
    games = sorted(
        (_game_from_raw(raw) for raw in raw_games),
        key=lambda game: game.end_time,
        reverse=True,
    )

    written = 0
    for game in games:
        year_dir = root / game.end_time.strftime("%Y")
        month_dir = year_dir / game.end_time.strftime("%m")
        month_dir.mkdir(parents=True, exist_ok=True)
        path = month_dir / _filename(game)
        path.write_text(_game_note(game), encoding="utf-8")
        written += 1

    return {
        "status": "ok",
        "username": CHESS_USERNAME,
        "destination": str(root),
        "games_received": len(games),
        "games_written": written,
        "reset": reset,
        "structure": "Echecs/YYYY/MM/date - ECO - adversaire.md",
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Reconstruit la bibliothèque Chess.com chronologique dans Obsidian"
    )
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Supprime tout le contenu actuel du dossier Echecs avant reconstruction.",
    )
    args = parser.parse_args(argv)
    print(sync_chess_to_obsidian(limit=args.limit, reset=args.reset))


if __name__ == "__main__":
    main()
