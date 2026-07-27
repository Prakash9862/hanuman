from __future__ import annotations

import argparse
import io
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

import chess.pgn

from hanuman.models.chess import (
    ChessGame,
    chess_game_disambiguated_filename,
    chess_game_historical_filename,
    safe_chess_filename_part,
)
from hanuman.services.atomic_write_service import atomic_write_text
from hanuman.services.chess_generated_frontmatter_service import (
    CHESS_MANAGED_TAG_PREFIXES,
    ChessGeneratedFrontmatterError,
    update_generated_frontmatter,
)
from hanuman.services.chess_index_service import write_chess_indexes
from hanuman.services.chess_insight_storage_service import (
    ChessInsightBlockError,
    extract_insight_block,
    parse_chess_note_insight_metadata,
)
from hanuman.services.chess_path_safety_service import resolve_safe_destination
from hanuman.services.chess_vault_reader_service import read_chess_vault
from hanuman.services.core.chess_service import ChessService
from hanuman.services.delimited_zone_service import (
    DelimitedZoneError,
    extract_delimited_zone,
    replace_delimited_zone,
)

CHESS_USERNAME = "prakasch"
ANALYSIS_START = "<!-- HANUMAN_CHESS_ANALYSIS_START -->"
ANALYSIS_END = "<!-- HANUMAN_CHESS_ANALYSIS_END -->"
GAME_START = "<!-- HANUMAN_CHESS_GAME_START -->"
GAME_END = "<!-- HANUMAN_CHESS_GAME_END -->"
GAME_FRONTMATTER_KEYS = frozenset(
    {
        "type",
        "cssclasses",
        "date",
        "year",
        "month",
        "platform",
        "username",
        "game_id",
        "result",
        "color",
        "opponent",
        "white",
        "black",
        "white_elo",
        "black_elo",
        "eco",
        "opening",
        "time_control",
        "termination",
        "analysis_status",
        "chess_url",
        "tags",
    }
)
OBSIDIAN_ROOT = Path("/home/vince/Prakash/projets/Obsidian_Priv-/Echecs")


class UnsafeChessResetError(RuntimeError):
    """Levée lorsqu'une reconstruction destructive est demandée."""


class ChessGameNoteUpdateError(ValueError):
    """Signale une note de partie impossible à mettre à jour sans ambiguïté."""


@dataclass(frozen=True)
class HistoricalChessIdentity:
    state: Literal["valid", "absent", "invalid"]
    game_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class ProtectedHistoricalChessNote:
    path: Path
    reason: str


@dataclass(frozen=True)
class ChessGamePathSelection:
    games: tuple[tuple[ChessGame, Path], ...]
    protected_notes: tuple[ProtectedHistoricalChessNote, ...] = ()


def _chess_root() -> Path:
    configured = os.environ.get("CHESS_OBSIDIAN_PATH")
    if configured:
        return Path(configured).expanduser()

    configured_vault = os.environ.get("OBSIDIAN_VAULT_PATH")
    if configured_vault:
        return Path(configured_vault).expanduser() / "Echecs"

    return OBSIDIAN_ROOT.expanduser()


def _yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _game_from_raw(raw: dict[str, Any]) -> ChessGame:
    raw_game_id = raw["id"]
    game_id = "" if raw_game_id is None else str(raw_game_id).strip()
    if not game_id:
        raise ChessGameNoteUpdateError("Identifiant Chess vide ou invalide.")
    return ChessGame(
        game_id=game_id,
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
    try:
        return extract_delimited_zone(
            markdown,
            ANALYSIS_START,
            ANALYSIS_END,
            label="d’analyse Chess",
        )
    except DelimitedZoneError as exc:
        raise ChessGameNoteUpdateError(str(exc)) from exc


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


def _game_generated(
    game: ChessGame,
    analysis_block: str | None = None,
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

{GAME_START}
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
{GAME_END}'''


def _game_note(
    game: ChessGame,
    analysis_block: str | None = None,
    insight_block: str | None = None,
) -> str:
    analysis = analysis_block or _default_analysis()
    technical_block = f"\n\n{insight_block}" if insight_block is not None else ""
    return f"{_game_generated(game, analysis)}\n\n{analysis}{technical_block}\n"


def _historical_identity(markdown: str) -> HistoricalChessIdentity:
    if not markdown.startswith("---\n"):
        return HistoricalChessIdentity("invalid", reason="Frontmatter Chess absent ou invalide.")
    try:
        game_id = parse_chess_note_insight_metadata(markdown).game_id
    except ValueError as exc:
        return HistoricalChessIdentity("invalid", reason=str(exc))
    if game_id is None:
        return HistoricalChessIdentity("absent")
    if not game_id.strip():
        return HistoricalChessIdentity("invalid", reason="Identifiant Chess historique vide.")
    return HistoricalChessIdentity("valid", game_id=game_id.strip())


def _select_game_paths(root: Path, games: list[ChessGame]) -> ChessGamePathSelection:
    identities: dict[str, ChessGame] = {}
    for game in games:
        if not isinstance(game.game_id, str):
            raise ChessGameNoteUpdateError("Identifiant Chess vide ou invalide.")
        normalized_id = game.game_id.strip()
        if not normalized_id:
            raise ChessGameNoteUpdateError("Identifiant Chess vide ou invalide.")
        normalized_game = replace(game, game_id=normalized_id)
        previous = identities.get(normalized_id)
        if previous is not None and previous != normalized_game:
            raise ChessGameNoteUpdateError(f"Identité Chess contradictoire pour {normalized_id!r}.")
        identities[normalized_id] = normalized_game

    groups: dict[Path, list[ChessGame]] = {}
    for game in identities.values():
        historical = (
            root / game.year / game.end_time.strftime("%m") / (chess_game_historical_filename(game))
        )
        groups.setdefault(historical, []).append(game)

    selected: list[tuple[ChessGame, Path]] = []
    protected: list[ProtectedHistoricalChessNote] = []
    for historical, grouped in sorted(groups.items(), key=lambda item: str(item[0])):
        unique = {game.game_id: game for game in grouped}
        ordered = [unique[game_id] for game_id in sorted(unique)]
        historical = resolve_safe_destination(root, historical)
        historical_identity = HistoricalChessIdentity("absent")
        if historical.exists():
            if not historical.is_file():
                raise ChessGameNoteUpdateError(f"Destination de note non régulière : {historical}")
            historical_identity = _historical_identity(historical.read_text(encoding="utf-8"))
            if historical_identity.state == "invalid":
                protected.append(
                    ProtectedHistoricalChessNote(
                        historical,
                        historical_identity.reason or "Note Chess historique invalide.",
                    )
                )
                continue

        base_id = (
            historical_identity.game_id
            if historical_identity.state == "valid" and historical_identity.game_id in unique
            else None
        )
        if not historical.exists() and ordered:
            base_id = ordered[0].game_id

        for game in ordered:
            if game.game_id == base_id:
                path = historical
            else:
                path = historical.with_name(chess_game_disambiguated_filename(game))
                path = resolve_safe_destination(root, path)
            if path.exists():
                if not path.is_file():
                    raise ChessGameNoteUpdateError(f"Destination de note non régulière : {path}")
                stored_identity = _historical_identity(path.read_text(encoding="utf-8"))
                if stored_identity.state != "valid" or stored_identity.game_id != game.game_id:
                    raise ChessGameNoteUpdateError(
                        f"Collision d’identité Chess : {path} contient "
                        f"{stored_identity.game_id!r} ({stored_identity.state}), "
                        f"partie reçue {game.game_id!r}."
                    )
            selected.append((replace(game, note_filename=path.name), path))
    destinations: dict[Path, str] = {}
    for game, path in selected:
        previous_id = destinations.get(path)
        if previous_id is not None and previous_id != game.game_id:
            raise ChessGameNoteUpdateError(
                f"Collision de destination Chess : {path} vise "
                f"{previous_id!r} et {game.game_id!r}."
            )
        destinations[path] = game.game_id
    return ChessGamePathSelection(tuple(selected), tuple(protected))


def _updated_game_note(existing: str, game: ChessGame) -> str | None:
    analysis = _extract_analysis(existing)
    extract_insight_block(existing)
    generated_zone = extract_delimited_zone(
        _game_generated(game, analysis),
        GAME_START,
        GAME_END,
        label="de note Chess",
    )
    assert generated_zone is not None
    generated_note = _game_generated(game, analysis)
    try:
        updated_frontmatter = update_generated_frontmatter(
            existing,
            generated_note,
            owned_keys=GAME_FRONTMATTER_KEYS,
            label="de note Chess",
            managed_tag_prefixes=CHESS_MANAGED_TAG_PREFIXES,
        )
        updated = replace_delimited_zone(
            updated_frontmatter,
            generated_zone,
            GAME_START,
            GAME_END,
            label="de note Chess",
        )
    except (ChessGeneratedFrontmatterError, DelimitedZoneError) as exc:
        raise ChessGameNoteUpdateError(str(exc)) from exc
    return updated


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

    written = 0
    preserved_analyses = 0
    selection = _select_game_paths(root, games)
    protected_notes = [str(item.path.relative_to(root)) for item in selection.protected_notes]
    protected_diagnostics = [
        {"path": str(item.path.relative_to(root)), "reason": item.reason}
        for item in selection.protected_notes
    ]
    planned_notes: list[tuple[Path, str]] = []
    for game, path in selection.games:
        if path.exists():
            previous_markdown = path.read_text(encoding="utf-8")
            try:
                previous_analysis = _extract_analysis(previous_markdown)
                updated = _updated_game_note(previous_markdown, game)
            except (ChessGameNoteUpdateError, ChessInsightBlockError, UnicodeError) as exc:
                relative_path = str(path.relative_to(root))
                protected_notes.append(relative_path)
                protected_diagnostics.append({"path": relative_path, "reason": str(exc)})
                continue
            if updated is None:
                relative_path = str(path.relative_to(root))
                protected_notes.append(relative_path)
                protected_diagnostics.append(
                    {
                        "path": relative_path,
                        "reason": "Zone de partie Hanuman absente ; migration sûre requise.",
                    }
                )
                continue
            if previous_analysis:
                preserved_analyses += 1
            planned_notes.append((path, updated))
        else:
            planned_notes.append((path, _game_note(game)))

    for path, content in sorted(planned_notes, key=lambda item: str(item[0])):
        atomic_write_text(resolve_safe_destination(root, path), content)
        written += 1

    read_result = read_chess_vault(root)
    index_files = write_chess_indexes(root, list(read_result.games))

    return {
        "status": "ok",
        "username": CHESS_USERNAME,
        "destination": str(root),
        "games_received": len(games),
        "games_written": written,
        "games_protected": len(protected_notes),
        "protected_game_files": protected_notes,
        "protected_game_diagnostics": protected_diagnostics,
        "vault_games_usable": read_result.notes_usable,
        "vault_notes_ignored": read_result.notes_ignored,
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
