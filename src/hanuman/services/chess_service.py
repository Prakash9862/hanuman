import httpx
from hanuman.models.ping import PingResult  # ✅ Ajout typage propre
from hanuman.utils.decorators import trace_endpoint

CHESS_USERNAME = "prakash9862"
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

    elif response.status_code == 404:
        raise ValueError("User not found")

    raise RuntimeError(f"Unexpected status: {response.status_code}")
