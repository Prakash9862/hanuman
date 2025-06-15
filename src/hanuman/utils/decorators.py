# src/hanuman/utils/decorators.py

import logging
from datetime import UTC, datetime
from functools import wraps
from time import time
from typing import Callable, TypeVar, cast

from hanuman.models.ping import PingResult

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., PingResult])


def safe_ping(source: str) -> Callable[[F], F]:
    """
    Décorateur pour uniformiser la structure et le logging des fonctions de ping.
    Il capture les erreurs, ajoute un timestamp et une mesure de durée d'exécution.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> PingResult:
            start = time()
            try:
                result = func(*args, **kwargs)
                duration = int((time() - start) * 1000)

                logger.info(f"✅ Ping réussi : {source} [{duration} ms]")
                return PingResult(
                    ok=True,
                    source=source,
                    timestamp=datetime.now(UTC),
                    duration_ms=duration,
                    detail=result.detail if isinstance(result, PingResult) else None,
                    error=result.error if isinstance(result, PingResult) else None,
                )
            except Exception as e:
                duration = int((time() - start) * 1000)

                logger.error(f"❌ Ping échoué : {source} | {type(e).__name__}: {e}")
                return PingResult(
                    ok=False,
                    source=source,
                    timestamp=datetime.now(UTC),
                    duration_ms=duration,
                    error=str(e),
                )

        return cast(F, wrapper)

    return decorator
