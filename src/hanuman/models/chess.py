from __future__ import annotations

import datetime as dt
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


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
    note_filename: str | None = None

    @property
    def opponent(self) -> str:
        return self.black if self.color == "white" else self.white

    @property
    def year(self) -> str:
        return self.end_time.strftime("%Y")

    @property
    def month(self) -> str:
        return self.end_time.strftime("%Y-%m")


def safe_chess_filename_part(value: str) -> str:
    value = re.sub(r"[^\w\-. ]+", "", value, flags=re.UNICODE).strip()
    return re.sub(r"\s+", " ", value) or "partie"


def chess_game_filename(game: ChessGame) -> str:
    if game.note_filename is not None:
        return game.note_filename
    return chess_game_historical_filename(game)


def chess_game_historical_filename(game: ChessGame) -> str:
    date = game.end_time.strftime("%Y-%m-%d")
    return f"{date} - {game.eco} - {safe_chess_filename_part(game.opponent)}.md"


def chess_game_disambiguated_filename(game: ChessGame) -> str:
    historical = chess_game_historical_filename(game)
    suffix = hashlib.sha256(game.game_id.encode("utf-8")).hexdigest()[:8]
    return f"{historical[:-3]} - {suffix}.md"


def chess_game_path(root: Path, game: ChessGame) -> Path:
    return root / game.year / game.end_time.strftime("%m") / chess_game_filename(game)


def chess_game_note_link(game: ChessGame) -> str:
    note = chess_game_filename(game)[:-3]
    path = f"Echecs/{game.year}/{game.end_time.strftime('%m')}/{note}"
    label = (
        f"{game.end_time.strftime('%Y-%m-%d')} · {game.eco} · " f"{game.opponent} · {game.result}"
    )
    return f"[[{path}|{label}]]"
