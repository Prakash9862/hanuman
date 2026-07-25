from __future__ import annotations

import argparse
import datetime as dt
import io
import os
import re
import shutil
from collections import defaultdict
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

    @property
    def year(self) -> str:
        return self.end_time.strftime("%Y")

    @property
    def month(self) -> str:
        return self.end_time.strftime("%Y-%m")


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


def _game_link(game: ChessGame) -> str:
    path = f"Echecs/{game.year}/{game.end_time.strftime('%m')}/{_filename(game)[:-3]}"
    label = (
        f"{game.end_time.strftime('%Y-%m-%d')} · {game.eco} · "
        f"{game.opponent} · {game.result}"
    )
    return f"[[{path}|{label}]]"


def _default_analysis() -> str:
    return (
        f"{ANALYSIS_START}\n"
        "## Analyse Stockfish\n\n"
        "> [!stockfish] 🟡 Analyse en attente\n"
        "> Cette partie n’a pas encore été analysée.\n\n"
        "Analyse non encore lancée.\n"
        f"{ANALYSIS_END}"
    )


def _extract_analysis(markdown: str) -> str | None:
    if ANALYSIS_START not in markdown or ANALYSIS_END not in markdown:
        return None
    _, rest = markdown.split(ANALYSIS_START, 1)
    body, _ = rest.split(ANALYSIS_END, 1)
    return f"{ANALYSIS_START}{body}{ANALYSIS_END}"


def _analysis_done(analysis: str) -> bool:
    return "Analyse non encore lancée." not in analysis and "### Ton bilan" in analysis


def _result_label(result: str) -> str:
    return {
        "win": "🟢 Victoire",
        "loss": "🔴 Défaite",
        "draw": "🟡 Nulle",
    }.get(result, f"⚪ {result}")


def _color_label(color: str) -> str:
    return "⚪ Blancs" if color == "white" else "⚫ Noirs"


def _quoted_block(markdown: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in markdown.splitlines())


def _game_note(game: ChessGame, analysis_block: str | None = None) -> str:
    date = game.end_time.strftime("%Y-%m-%d")
    headers = _parse_headers(game.pgn)
    title = f"{date} — {game.eco} — {game.opponent}"
    opening = headers.get("Opening") or game.opening_name
    white_elo = headers.get("WhiteElo", "")
    black_elo = headers.get("BlackElo", "")
    termination = headers.get("Termination", "")
    analysis = analysis_block or _default_analysis()
    analysed = _analysis_done(analysis)
    opponent_slug = _safe(game.opponent)
    status = "analysed" if analysed else "pending"
    status_label = "🟢 Analyse terminée" if analysed else "🟡 Analyse en attente"
    headers_block = _quoted_block(_headers_table(headers))
    pgn_block = _quoted_block(game.pgn.strip())

    return f'''---
type: chess-game
cssclasses:
  - hanuman-chess
  - hanuman-chess-game
date: {date}
year: {game.year}
month: {game.month}
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
analysis_status: {status}
chess_url: {_yaml_quote(game.url)}
tags:
  - chess/game
  - chess/result/{game.result}
  - chess/color/{game.color}
  - chess/time/{_safe(game.time_control).replace(' ', '-').lower()}
  - chess/opening/{game.eco}
  - chess/year/{game.year}
  - chess/month/{game.month}
  - chess/analysis/{status}
---

# ♟️ {title}

> [!chess] Partie
> **{_result_label(game.result)}** · **{_color_label(game.color)}** · **{game.time_control}**  
> **{game.white}{f' ({white_elo})' if white_elo else ''}** contre **{game.black}{f' ({black_elo})' if black_elo else ''}**  
> **{game.eco} — {opening}**

> [!hanuman-nav] Navigation
> 🏠 [[Dashboard|Tableau de bord]] · 📅 [[_Index/Annees/{game.year}|{game.year}]] · 🗓️ [[_Index/Mois/{game.month}|{game.month}]] · ♟️ [[_Index/Ouvertures/{game.eco}|{game.eco}]] · 👤 [[_Index/Adversaires/{opponent_slug}|{game.opponent}]]

> [!stockfish] {status_label}
> **Statut :** {status_label}

## Résumé

| Élément | Détail |
|---|---|
| Résultat | {_result_label(game.result)} |
| Couleur | {_color_label(game.color)} |
| Adversaire | {game.opponent} |
| Cadence | {game.time_control} |
| Ouverture | {game.eco} — {opening} |
| Fin | {termination or 'non précisée'} |
| Partie | [Ouvrir sur Chess.com]({game.url}) |

> [!info]- En-têtes PGN
>
{headers_block}

> [!note]- PGN complet
>
> ```pgn
{pgn_block}
> ```

{analysis}
'''


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


def _write_indexes(root: Path, games: list[ChessGame]) -> int:
    index_root = root / "_Index"
    if index_root.exists():
        shutil.rmtree(index_root)

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
    groups = [
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
            (target / f"{key}.md").write_text(
                _index_note(kind, key, title, grouped_games),
                encoding="utf-8",
            )
            written += 1

    (root / "Dashboard.md").write_text(_dashboard(games), encoding="utf-8")
    return written + 1


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

    index_files = _write_indexes(root, games)

    return {
        "status": "ok",
        "username": CHESS_USERNAME,
        "destination": str(root),
        "games_received": len(games),
        "games_written": written,
        "analyses_preserved": preserved_analyses,
        "index_files_written": index_files,
        "reset": reset,
        "structure": "Echecs/YYYY/MM/date - ECO - adversaire.md + _Index",
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Reconstruit la bibliothèque Chess.com et son graphe Obsidian"
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
