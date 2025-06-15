import httpx

from hanuman.utils.decorators import safe_ping

CHESS_USERNAME = "prakash9862"
CHESS_API_URL = f"https://api.chess.com/pub/player/{CHESS_USERNAME}"


@safe_ping("chess")
def ping_chess() -> dict:
    response = httpx.get(CHESS_API_URL, timeout=5)

    if response.status_code == 200:
        user = response.json()
        return {"username": user.get("username", None)}

    elif response.status_code == 404:
        raise ValueError("User not found")

    raise RuntimeError(f"Unexpected status: {response.status_code}")
