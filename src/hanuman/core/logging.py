# src/hanuman/core/logging.py

import logging
import sys
from pathlib import Path
from typing import (
    Any,
    Callable,
    Mapping,
    MutableMapping,
    Optional,
    Tuple,
    Union,
)

import structlog
from structlog.contextvars import merge_contextvars
from structlog.processors import JSONRenderer, TimeStamper
from structlog.stdlib import LoggerFactory

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Typage conforme à structlog.typing.Processor (doc officielle v25.4.0)
Processor = Callable[
    [Any, str, MutableMapping[str, Any]],
    Union[
        Mapping[str, Any],
        str,
        bytes,
        bytearray,
        Tuple[Any, ...],
    ],
]


def configure_logging(debug: bool = True) -> None:
    """
    Configure le système de logging structlog pour l'application Hanuman.
    - Logs vers stdout + fichiers séparés DEBUG et ERROR
    - Format console en dev, JSON en prod
    """
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_DIR / "hanuman_debug.log", mode="a", encoding="utf-8"),
            logging.FileHandler(LOG_DIR / "hanuman_error.log", mode="a", encoding="utf-8"),
        ],
    )

    processors: list[Processor] = [
        merge_contextvars,
        structlog.processors.add_log_level,
        TimeStamper(fmt="iso"),
    ]

    renderer: Processor = structlog.dev.ConsoleRenderer() if debug else JSONRenderer()
    processors.append(renderer)

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> Any:
    """
    Retourne un logger structlog configuré pour Hanuman.
    Note : structlog.get_logger retourne un proxy typé dynamiquement (LazyLogger)
    """
    return structlog.get_logger(name or "hanuman")
