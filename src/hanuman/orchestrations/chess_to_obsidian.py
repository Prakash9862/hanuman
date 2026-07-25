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


def _chess_root() -> Path:
    configured = os.environ.get("CHESS_OBSIDIAN_PATH")
    if configured:
        return Path(configured).expanduser().resolve()

    configured_vault = os.environ.get("OBSIDIAN_VAULT_PATH")
    if configured_vault:
        return (Path(configured_vault).expanduser() / "Echecs").resolve()

    return OBSIDIAN_ROOT.expanduser().resolve()


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


def _default_analysis() -> str:
    return (
        f"{ANALYSIS_START}\n"
        "## Analyse Stockfish\n\n"
        "Analyse non encore lancée.\n"
        f"{ANALYSIS_END}"
    )


def _extract_analysis(markdown: str) -> str | None:
    if ANALYSIS_START not in markdown or ANALYSIS_END not in markdown:
        return None
    _, rest = markdown.split(ANALYSIS_START, 1)
    body, _ = rest.split(ANALYSIS_END, 1)
    return f"{ANALYSIS_START}{body}{ANALYSIS_END}"


def _game_note(game: ChessGame, analysis_block: str | None = None) -> str:
    date = game.end_time.strftime("%Y-%m-%d")
    headers = _parse_headers(game.pgn)
    title = f"{date} — {game.eco} — {game.opponent}"
    opening = headers.get("Opening") or game.opening_name
    white_elo = headers.get("WhiteElo", "")
    black_elo = headers.get("BlackElo", "")
    termination = headers.get("Termination", "")
    analysis = analysis_block or _default_analysis()

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

{analysis}
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
    raw_games = ChessService().get_latest_games(username=CHESS_USERNAME, limit=limit)
    games = sorted(
        (_game_from_raw(raw) for raw in raw_games),
        key=lambda game: game.end_time,
        reverse=True,
    )[:limit]

    if reset:
        _reset_root(root)
    else:
        root.mkdir(parents=True, exist_ok=True)

    written = 0
    preserved_analyses = 0
    for game in games:
        month_dir = root / game.end_time.strftime("%Y") / game.end_time.strftime("%m")
        month_dir.mkdir(parents=True, exist_ok=True)
        path = month_dir / _filename(game)
        previous_analysis = None
        if path.exists() and not reset:
            previous_analysis = _extract_analysis(path.read_text(encoding="utf-8"))
            if previous_analysis is not None:
                preserved_analyses += 1
        path.write_text(_game_note(game, previous_analysis), encoding="utf-8")
        written += 1

    return {
        "status": "ok",
        "username": CHESS_USERNAME,
        "destination": str(root),
        "games_received": len(games),
        "games_written": written,
        "analyses_preserved": preserved_analyses,
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
    if args.reset:
        result = sync_chess_to_obsidian(limit=args.limit, reset=True)
    else:
        result = sync_chess_to_obsidian(limit=args.limit)
    print(result)


if __name__ == "__main__":
    main()
