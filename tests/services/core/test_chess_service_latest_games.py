from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

from hanuman.services.core.chess_service import ChessService


class FakeResponse:
    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    def raise_for_status(self) -> None:  # comme httpx.Response
        return None

    def json(self) -> Dict[str, Any]:
        return self._data


class FakeClient:
    def __init__(self) -> None:
        self.calls: List[str] = []

    def get(self, url: str) -> FakeResponse:
        self.calls.append(url)

        # 1) archives
        if "games/archives" in url:
            return FakeResponse(
                {
                    "archives": [
                        "https://api.chess.com/pub/player/prakasch/games/2025/10"
                    ]
                }
            )

        # 2) données du mois
        if "games/2025/10" in url:
            games = [
                {
                    "uuid": "game-1",
                    "end_time": 1_700_000_000,
                    "white": {"username": "Prakasch", "result": "win"},
                    "black": {"username": "Opponent1", "result": "checkmated"},
                    "pgn": '[Event ""]\n[ECO "A45"]\n[Opening "Trompowsky Attack"]\n\n1. d4 d5 2. Bg5',
                    "time_class": "blitz",
                    "url": "https://www.chess.com/game/1",
                },
                {
                    # joueur côté noir → doit être traité
                    "last_move_at": 1_700_000_100,
                    "white": {"username": "Other", "result": "resigned"},
                    "black": {"username": "prakasch", "result": "agreed"},
                    "pgn": '[Event ""]\n[ECO "B12"]\n\n1. e4 c6',
                    "time_control": "600+0",
                    "url": "https://www.chess.com/game/2",
                },
                {
                    # partie qui ne concerne pas l'utilisateur → ignorée
                    "end_time": 1_700_000_200,
                    "white": {"username": "Someone", "result": "win"},
                    "black": {"username": "Else", "result": "checkmated"},
                    "pgn": "",
                    "time_class": "rapid",
                    "url": "https://www.chess.com/game/3",
                },
            ]
            return FakeResponse({"games": games})

        raise AssertionError(f"URL inattendue: {url}")


def test_chess_service_extract_opening_and_result_mapping() -> None:
    client = FakeClient()
    service = ChessService(client=client)

    games = service.get_latest_games("Prakasch", limit=10)

    # On a bien filtré la partie qui ne concerne pas l'utilisateur
    assert len(games) == 2

    g1 = games[0]
    g2 = games[1]

    # Partie 1 : côté blanc, victoire, ouverture complète
    assert g1["color"] == "white"
    assert g1["result"] == "win"
    assert g1["eco"] == "A45"
    assert g1["opening_name"] == "Trompowsky Attack"
    assert g1["time_control"] == "blitz"
    assert g1["url"] == "https://www.chess.com/game/1"
    assert isinstance(g1["end_time"], dt.datetime)

    # Partie 2 : côté noir, résultat "agreed" → draw, pas de nom mais ECO
    assert g2["color"] == "black"
    assert g2["result"] == "draw"
    assert g2["eco"] == "B12"
    # Fallback: opening_name == ECO si pas de [Opening "..."]
    assert g2["opening_name"] == "B12"
    assert g2["time_control"] == "600+0"
    assert g2["url"] == "https://www.chess.com/game/2"
    assert isinstance(g2["end_time"], dt.datetime)

    # On a bien appelé l'endpoint archives + un mois
    assert any("games/archives" in url for url in client.calls)
    assert any("games/2025/10" in url for url in client.calls)
