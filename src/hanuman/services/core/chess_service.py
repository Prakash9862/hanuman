from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

import httpx

from hanuman.models.ping import PingResult  # ✅ Ajout typage propre
from hanuman.utils.decorators import trace_endpoint

# --- Ping de base déjà utilisé ailleurs ---

CHESS_USERNAME = "prakasch"
CHESS_API_URL = f"https://api.chess.com/pub/player/{CHESS_USERNAME}"


@trace_endpoint("chess", catch=True)
def ping_chess() -> PingResult:
    response = httpx.get(CHESS_API_URL, timeout=5)

    if response.status_code == 200:
        user = response.json()
        return PingResult(
            ok=True,
            source="chess",
            detail={"username": user.get("username", None)},
        )

    if response.status_code == 404:
        raise ValueError("User not found")

    raise RuntimeError(f"Unexpected status: {response.status_code}")


# --- Nouveau service pour les parties ---

class ChessService:
    """
    Service minimal pour récupérer les dernières parties Chess.com
    et les normaliser pour l'orchestration Obsidian.

    La méthode importante est:
        get_latest_games(username, limit) -> list[dict[str, Any]]
    """

    BASE_API = "https://api.chess.com/pub"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=10)

    def _get_archives(self, username: str) -> List[str]:
        """Retourne la liste des URL d'archives mensuelles de l'utilisateur."""
        url = f"{self.BASE_API}/player/{username}/games/archives"
        resp = self.client.get(url)
        resp.raise_for_status()
        data = resp.json()
        archives = data.get("archives", [])
        return list(archives)

    def _normalize_result(self, player_result: str) -> str:
        """Mappe les résultats Chess.com en win/loss/draw pour TOI."""
        r = player_result.lower()
        if r == "win":
            return "win"
        if r in {
            "agreed",
            "stalemate",
            "repetition",
            "insufficient",
            "50move",
            "timevsinsufficient",
        }:
            return "draw"
        return "loss"

    def _extract_opening(self, pgn: str) -> tuple[str, str]:
        """Extrait ECO et nom d'ouverture à partir du PGN."""
        eco = ""
        opening_name = ""
        for raw_line in pgn.splitlines():
            line = raw_line.strip()  # 🔥 on nettoie les espaces au début/fin
            if line.startswith("[ECO "):
                try:
                    eco = line.split('"', 2)[1]
                except IndexError:
                    pass
            elif line.startswith("[Opening "):
                try:
                    opening_name = line.split('"', 2)[1]
                except IndexError:
                    pass

        # Fallback : si pas de nom mais un ECO, on met au moins l'ECO comme nom
        if not opening_name and eco:
            opening_name = eco

        return eco, opening_name



    def get_latest_games(self, username: str, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Retourne une liste de dicts avec les champs attendus par chess_to_obsidian.py :

        - id: str
        - end_time: datetime
        - white: nom du joueur blanc
        - black: nom du joueur noir
        - result: "win" / "loss" / "draw" (pour TOI)
        - color: "white" / "black" (ta couleur dans la partie)
        - opening_name: str
        - eco: str
        - time_control: str (blitz, rapid, etc.)
        - url: str
        """
        archives = self._get_archives(username)
        games: List[Dict[str, Any]] = []

        # on parcourt les mois du plus récent au plus ancien
        for month_url in reversed(archives):
            resp = self.client.get(month_url)
            resp.raise_for_status()
            month_data = resp.json()

            for g in month_data.get("games", []):
                white = g.get("white", {}) or {}
                black = g.get("black", {}) or {}

                uname = username.lower()
                color: str | None = None
                player_side: Dict[str, Any] | None = None

                if str(white.get("username", "")).lower() == uname:
                    color = "white"
                    player_side = white
                elif str(black.get("username", "")).lower() == uname:
                    color = "black"
                    player_side = black
                else:
                    # partie qui ne te concerne pas → on skip
                    continue

                player_result = str(player_side.get("result", ""))
                result = self._normalize_result(player_result)

                # Temps de fin
                end_ts = g.get("end_time") or g.get("last_move_at")
                if end_ts is None:
                    end_time = dt.datetime.utcnow()
                else:
                    end_time = dt.datetime.fromtimestamp(end_ts)

                # Ouverture et ECO depuis le PGN
                pgn = g.get("pgn", "") or ""
                eco, opening_name = self._extract_opening(pgn)

                time_control = g.get("time_class") or g.get("time_control", "")
                url = g.get("url", "") or ""
                game_id = g.get("uuid") or url or str(end_ts)

                games.append(
                    {
                        "id": str(game_id),
                        "end_time": end_time,
                        "white": str(white.get("username", "")),
                        "black": str(black.get("username", "")),
                        "result": result,           # "win"/"loss"/"draw" pour TOI
                        "color": color,             # "white"/"black" pour TOI
                        "opening_name": opening_name,
                        "eco": eco,
                        "time_control": time_control,
                        "url": url,
                    }
                )

                if len(games) >= limit:
                    return games

        return games
