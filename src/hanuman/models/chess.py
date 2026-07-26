from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


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
