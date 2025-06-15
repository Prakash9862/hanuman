import httpx

from hanuman.core.config import get_env_var
from hanuman.utils.decorators import safe_ping

GITHUB_API_URL = "https://api.github.com/user"


@safe_ping("github")
def ping_github() -> dict:
    token = get_env_var("GITHUB_TOKEN")
    if not token:
        raise ValueError("Missing token")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    response = httpx.get(GITHUB_API_URL, headers=headers, timeout=5)

    if response.status_code == 200:
        return {"login": response.json().get("login")}

    elif response.status_code == 401:
        raise ValueError("Unauthorized")

    raise RuntimeError(f"Unexpected status: {response.status_code}")
