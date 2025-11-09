# src/hanuman/utils/decorators.py

import inspect
from datetime import UTC, datetime
from functools import wraps
from time import time
from typing import Any, Callable, Optional, TypeVar, cast

from fastapi import Request

from hanuman.core.config import settings
from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.utils.log_helpers import get_ip, get_method, get_path

F = TypeVar("F", bound=Callable[..., Any])


def trace_endpoint(source: str, catch: bool = True) -> Callable[[F], F]:
    """
    Décorateur unique pour :
    - logger automatiquement toute exécution d'endpoint ou de fonction service
    - injecter IP, endpoint, méthode, debug_mode si `Request` est présent
    - capturer les erreurs si catch=True (retourne PingResult en cas d'échec)
    - mesurer la durée d'exécution
    """

    def decorator(func: F) -> F:
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args: object, **kwargs: object) -> Any:
            start = time()
            request: Optional[Request] = next((a for a in args if isinstance(a, Request)), None)
            logger = get_logger(source)

            logger.bind(
                ip=get_ip(request),
                endpoint=get_path(request),
                method=get_method(request),
                debug_mode=settings.debug,
            ).info("📥 Requête reçue")

            try:
                result = await func(*args, **kwargs)
                duration = int((time() - start) * 1000)

                if isinstance(result, PingResult):
                    return PingResult(
                        **result.model_dump(),
                        duration_ms=duration,
                        timestamp=datetime.now(UTC),
                    )

                logger.info(f"✅ Exécution réussie : {source} [{duration} ms]")
                return result

            except Exception as e:
                duration = int((time() - start) * 1000)
                logger.error(f"❌ Erreur {type(e).__name__} dans {source} | {str(e)}")

                if catch:
                    return PingResult(
                        ok=False,
                        source=source,
                        duration_ms=duration,
                        timestamp=datetime.now(UTC),
                        error=str(e),
                    )
                raise

        @wraps(func)
        def sync_wrapper(*args: object, **kwargs: object) -> Any:
            start = time()
            request: Optional[Request] = next((a for a in args if isinstance(a, Request)), None)
            logger = get_logger(source)

            logger.bind(
                ip=get_ip(request),
                endpoint=get_path(request),
                method=get_method(request),
                debug_mode=settings.debug,
            ).info("📥 Requête reçue")

            try:
                result = func(*args, **kwargs)
                duration = int((time() - start) * 1000)

                if isinstance(result, PingResult):
                    return PingResult(
                        **result.model_dump(),
                        duration_ms=duration,
                        timestamp=datetime.now(UTC),
                    )

                logger.info(f"✅ Exécution réussie : {source} [{duration} ms]")
                return result

            except Exception as e:
                duration = int((time() - start) * 1000)
                logger.error(f"❌ Erreur {type(e).__name__} dans {source} | {str(e)}")

                if catch:
                    return PingResult(
                        ok=False,
                        source=source,
                        duration_ms=duration,
                        timestamp=datetime.now(UTC),
                        error=str(e),
                    )
                raise

        return cast(F, async_wrapper if is_async else sync_wrapper)

    return decorator
