import httpx

from hanuman.core.config import get_env_var
from hanuman.models.ping import PingResult  # ✅ le bon modèle
from hanuman.utils.decorators import safe_ping

NOTION_API_URL = "https://api.notion.com/v1/users/me"
NOTION_VERSION = "2022-06-28"


@safe_ping("notion")
def ping_notion() -> PingResult:
    token = get_env_var("NOTION_TOKEN")
    if not token:
        raise ValueError("Missing token")

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
    }

    response = httpx.get(NOTION_API_URL, headers=headers, timeout=5)

    if response.status_code == 200:
        return PingResult(ok=True, source="notion", detail={"user": response.json()})
    elif response.status_code == 401:
        raise ValueError("Unauthorized")

    raise RuntimeError(f"Unexpected status: {response.status_code}")
