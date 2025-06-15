import httpx

from hanuman.core.config import get_env_var
from hanuman.utils.decorators import safe_ping

OPENAI_API_URL = "https://api.openai.com/v1/models"


@safe_ping("openai")
def ping_openai() -> dict:
    token = get_env_var("OPENAI_TOKEN")
    if not token:
        raise ValueError("Missing token")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = httpx.get(OPENAI_API_URL, headers=headers, timeout=5)

    if response.status_code == 200:
        models = response.json()
        return {"model_count": len(models.get("data", []))}

    elif response.status_code == 401:
        raise ValueError("Unauthorized")

    raise RuntimeError(f"Unexpected status: {response.status_code}")
