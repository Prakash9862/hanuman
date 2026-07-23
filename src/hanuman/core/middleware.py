from typing import Awaitable, Callable

from fastapi import Request, Response

from hanuman.core.logging import get_logger

logger = get_logger(__name__)


async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # Libellé exact attendu par le test
    logger.info("Requête reçue")
    # Log d'entrée structuré
    logger.info({"method": request.method, "url": str(request.url), "event": "Requête entrante"})
    response: Response = await call_next(request)
    # Log de sortie structuré
    logger.info({"status_code": response.status_code, "event": "Réponse sortante"})
    return response
