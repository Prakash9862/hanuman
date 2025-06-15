import httpx

from hanuman.core.config import get_env_var
from hanuman.utils.decorators import safe_ping
from hanuman.models.ping import PingResult  # ✅ Modèle centralisé

GITHUB_API_URL = "https://api.github.com/user"


@safe_ping("github")
def ping_github() -> PingResult:
    token = get_env_var("GITHUB_TOKEN")
    if not token:
        raise ValueError("Missing token")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    response = httpx.get(GITHUB_API_URL, headers=headers, timeout=5)

    if response.status_code == 200:
        login = response.json().get("login", "inconnu")
        return PingResult(ok=True, source="github", detail={"login": login})

    elif response.status_code == 401:
        raise ValueError("Unauthorized")

    raise RuntimeError(f"Unexpected status: {response.status_code}")
