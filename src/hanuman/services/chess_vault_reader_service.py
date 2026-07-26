from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from hanuman.models.chess import ChessGame, chess_game_path


@dataclass(frozen=True)
class IgnoredChessNote:
    path: Path
    reason: str


@dataclass(frozen=True)
class ChessVaultReadResult:
    notes_discovered: int
    games: tuple[ChessGame, ...]
    ignored_notes: tuple[IgnoredChessNote, ...]

    @property
    def notes_usable(self) -> int:
        return len(self.games)

    @property
    def notes_ignored(self) -> int:
        return len(self.ignored_notes)


class ChessVaultNoteError(ValueError):
    """Signale une note qui ne permet pas de reconstruire un ChessGame."""


def _scalar(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        decoded = json.loads(value)
        if not isinstance(decoded, str):
            raise ChessVaultNoteError("Valeur de frontmatter non textuelle.")
        return decoded
    return value


def _frontmatter(markdown: str) -> dict[str, str] | None:
    if not markdown.startswith("---\n"):
        return None
    end = markdown.find("\n---\n", 4)
    if end < 0:
        raise ChessVaultNoteError("Frontmatter incomplet.")
    values: dict[str, str] = {}
    for line in markdown[4:end].splitlines():
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        try:
            values[key.strip()] = _scalar(value)
        except (json.JSONDecodeError, ChessVaultNoteError) as exc:
            raise ChessVaultNoteError(f"Valeur invalide pour {key.strip()}.") from exc
    return values


def _required(values: dict[str, str], key: str) -> str:
    value = values.get(key, "").strip()
    if not value:
        raise ChessVaultNoteError(f"Champ obligatoire absent : {key}.")
    return value


def read_chess_game_note(root: Path, path: Path) -> ChessGame | None:
    markdown = path.read_text(encoding="utf-8")
    values = _frontmatter(markdown)
    if values is None or values.get("type") != "chess-game":
        return None

    try:
        end_time = dt.datetime.strptime(_required(values, "date"), "%Y-%m-%d").replace(
            tzinfo=dt.timezone.utc
        )
    except ValueError as exc:
        raise ChessVaultNoteError("Date Chess invalide, format YYYY-MM-DD attendu.") from exc

    color = _required(values, "color")
    if color not in {"white", "black"}:
        raise ChessVaultNoteError("Couleur Chess invalide.")
    result = _required(values, "result")
    if result not in {"win", "draw", "loss"}:
        raise ChessVaultNoteError("Résultat Chess invalide.")

    game = ChessGame(
        game_id=_required(values, "game_id"),
        end_time=end_time,
        white=_required(values, "white"),
        black=_required(values, "black"),
        result=result,
        color=cast(Literal["white", "black"], color),
        opening_name=_required(values, "opening"),
        eco=_required(values, "eco"),
        time_control=_required(values, "time_control"),
        url=values.get("chess_url", ""),
        pgn="",
    )
    if chess_game_path(root, game) != path:
        raise ChessVaultNoteError("Le chemin ne correspond pas aux métadonnées de la partie.")
    return game


def read_chess_vault(root: Path) -> ChessVaultReadResult:
    candidates = sorted(
        path
        for year in root.iterdir()
        if year.is_dir() and len(year.name) == 4 and year.name.isdigit()
        for month in year.iterdir()
        if month.is_dir() and len(month.name) == 2 and month.name.isdigit()
        for path in month.glob("*.md")
        if path.is_file()
    )
    games: list[ChessGame] = []
    ignored: list[IgnoredChessNote] = []
    for path in candidates:
        try:
            game = read_chess_game_note(root, path)
        except (ChessVaultNoteError, OSError, UnicodeError) as exc:
            ignored.append(IgnoredChessNote(path, str(exc)))
            continue
        if game is None:
            ignored.append(IgnoredChessNote(path, "Note non échiquéenne."))
        else:
            games.append(game)
    games.sort(key=lambda game: (game.end_time, game.game_id), reverse=True)
    return ChessVaultReadResult(len(candidates), tuple(games), tuple(ignored))
