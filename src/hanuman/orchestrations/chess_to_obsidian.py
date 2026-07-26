from __future__ import annotations

import argparse
import io
import os
from pathlib import Path
from typing import Any

import chess.pgn

from hanuman.models.chess import (
    ChessGame,
    chess_game_filename,
    chess_game_path,
    safe_chess_filename_part,
)
from hanuman.services.atomic_write_service import atomic_write_text
from hanuman.services.chess_index_service import write_chess_indexes
from hanuman.services.chess_insight_storage_service import extract_insight_block
from hanuman.services.core.chess_service import ChessService

CHESS_USERNAME = "prakasch"
ANALYSIS_START = "<!-- HANUMAN_CHESS_ANALYSIS_START -->"
ANALYSIS_END = "<!-- HANUMAN_CHESS_ANALYSIS_END -->"
OBSIDIAN_ROOT = Path("/home/vince/Prakash/projets/Obsidian_Priv-/Echecs")


class UnsafeChessResetError(RuntimeError):
    """Levée lorsqu'une reconstruction destructive est demandée."""


def _chess_root() -> Path:
    configured = os.environ.get("CHESS_OBSIDIAN_PATH")
    if configured:
        return Path(configured).expanduser().resolve()

    configured_vault = os.environ.get("OBSIDIAN_VAULT_PATH")
    if configured_vault:
        return (Path(configured_vault).expanduser() / "Echecs").resolve()

    return OBSIDIAN_ROOT.expanduser().resolve()


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


def _game_note(
    game: ChessGame,
    analysis_block: str | None = None,
    insight_block: str | None = None,
) -> str:
    date = game.end_time.strftime("%Y-%m-%d")
    headers = _parse_headers(game.pgn)
    title = f"{date} — {game.eco} — {game.opponent}"
    opening = headers.get("Opening") or game.opening_name
    white_elo = headers.get("WhiteElo", "")
    black_elo = headers.get("BlackElo", "")
    termination = headers.get("Termination", "")
    analysis = analysis_block or _default_analysis()
    analysed = _analysis_done(analysis)
    status = "analysed" if analysed else "pending"
    status_label = "🟢 Analyse terminée" if analysed else "🟡 Analyse en attente"
    headers_block = _quoted_block(_headers_table(headers))
    pgn_block = _quoted_block(game.pgn.strip())
    technical_block = f"\n\n{insight_block}" if insight_block is not None else ""

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
  - chess/time/{safe_chess_filename_part(game.time_control).replace(' ', '-').lower()}
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
> 🏠 [[Echecs/_Index/Dashboard|Tableau de bord]] · 👤 [[Echecs/_Index/Profil échiquéen|Profil échiquéen]] · ♟️ [[Echecs/_Index/Ouvertures/{game.eco}|{game.eco}]]

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

{analysis}{technical_block}
'''


def sync_chess_to_obsidian(limit: int = 200, reset: bool = False) -> dict[str, Any]:
    if reset:
        raise UnsafeChessResetError(
            "Réinitialisation Chess refusée : la migration Obsidian est non destructive."
        )

    root = _chess_root()
    raw_games = ChessService().get_latest_games(username=CHESS_USERNAME, limit=limit)
    games = sorted(
        (_game_from_raw(raw) for raw in raw_games),
        key=lambda game: game.end_time,
        reverse=True,
    )[:limit]

    root.mkdir(parents=True, exist_ok=True)

    written = 0
    preserved_analyses = 0
    for game in games:
        month_dir = chess_game_path(root, game).parent
        month_dir.mkdir(parents=True, exist_ok=True)
        path = month_dir / chess_game_filename(game)
        previous_analysis = None
        previous_insights = None
        if path.exists():
            previous_markdown = path.read_text(encoding="utf-8")
            previous_analysis = _extract_analysis(previous_markdown)
            previous_insights = extract_insight_block(previous_markdown)
            if previous_analysis is not None:
                preserved_analyses += 1
        atomic_write_text(
            path,
            _game_note(game, previous_analysis, previous_insights),
        )
        written += 1

    index_files = write_chess_indexes(root, games)

    return {
        "status": "ok",
        "username": CHESS_USERNAME,
        "destination": str(root),
        "games_received": len(games),
        "games_written": written,
        "analyses_preserved": preserved_analyses,
        "index_files_written": index_files,
        "reset": reset,
        "structure": (
            "Echecs/YYYY/MM/date - ECO - adversaire.md + "
            "_Index/Dashboard, Profil et vues thématiques"
        ),
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
        parser.error("--reset est désactivé : la migration Chess Obsidian est non destructive.")
    result = sync_chess_to_obsidian(limit=args.limit)
    print(result)


if __name__ == "__main__":
    main()
