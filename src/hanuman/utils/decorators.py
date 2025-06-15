# src/hanuman/utils/decorators.py

import logging
from datetime import UTC, datetime
from functools import wraps
from time import time

from hanuman.models.ping import PingResult

logger = logging.getLogger(__name__)


def safe_ping(source: str):
    """
    Décorateur pour uniformiser la structure et le logging des fonctions de ping.
    Il capture les erreurs, ajoute un timestamp et une mesure de durée d'exécution.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
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
                    detail=result,
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

        return wrapper

    return decorator
