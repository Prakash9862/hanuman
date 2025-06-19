import httpx

from hanuman.core.config import settings
from hanuman.models.ping import PingResult  # ✅ le bon modèle
from hanuman.utils.decorators import trace_endpoint

NOTION_API_URL = "https://api.notion.com/v1/users/me"
NOTION_VERSION = "2022-06-28"


@trace_endpoint("notion", catch=True)
def ping_notion() -> PingResult:
    token = settings.notion_token
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
