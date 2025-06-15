import logging

import httpx

from hanuman.utils.decorators import safe_ping

logger = logging.getLogger(__name__)
WIKIPEDIA_URL = "https://fr.wikipedia.org/api/rest_v1/page/summary/OpenAI"


@safe_ping("wikipedia")
def ping_wikipedia() -> dict:
    response = httpx.get(WIKIPEDIA_URL, timeout=5)

    if response.status_code == 200:
        data = response.json()
        return {"title": data.get("title")}

    elif response.status_code == 404:
        raise ValueError("Article non trouvé")

    else:
        raise RuntimeError(f"Unexpected status: {response.status_code}")
