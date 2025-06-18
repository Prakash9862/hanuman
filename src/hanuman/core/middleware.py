import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from structlog import get_logger

logger = get_logger("hanuman")


async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:

    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    logger.info(
        "📨 Requête entrante", method=request.method, url=str(request.url), request_id=request_id
    )

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error("💥 Erreur pendant la requête", error=str(e), request_id=request_id)
        raise

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "📤 Réponse sortante",
        status_code=response.status_code,
        duration_ms=duration_ms,
        request_id=request_id,
    )
    return response
