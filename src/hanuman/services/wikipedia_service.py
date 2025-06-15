import logging

import httpx

from hanuman.models.ping import PingResult  # ✅ Modèle structuré
from hanuman.utils.decorators import safe_ping

logger = logging.getLogger(__name__)
WIKIPEDIA_URL = "https://fr.wikipedia.org/api/rest_v1/page/summary/OpenAI"


@safe_ping("wikipedia")
def ping_wikipedia() -> PingResult:
    response = httpx.get(WIKIPEDIA_URL, timeout=5)

    if response.status_code == 200:
        data = response.json()
        return PingResult(ok=True, source="wikipedia", detail={"title": data.get("title")})

    elif response.status_code == 404:
        raise ValueError("Article non trouvé")

    raise RuntimeError(f"Unexpected status: {response.status_code}")
