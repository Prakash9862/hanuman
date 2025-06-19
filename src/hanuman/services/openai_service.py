import httpx

from hanuman.core.config import settings
from hanuman.models.ping import PingResult  # ✅ Import modèle centralisé
from hanuman.utils.decorators import trace_endpoint

OPENAI_API_URL = "https://api.openai.com/v1/models"


@trace_endpoint("openai", catch=True)
def ping_openai() -> PingResult:
    token = settings.openai_api_key
    if not token:
        raise ValueError("Missing token")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = httpx.get(OPENAI_API_URL, headers=headers, timeout=5)

    if response.status_code == 200:
        models = response.json()
        return PingResult(
            ok=True,
            source="openai",
            detail={"model_count": len(models.get("data", []))},
        )

    elif response.status_code == 401:
        raise ValueError("Unauthorized")

    raise RuntimeError(f"Unexpected status: {response.status_code}")
