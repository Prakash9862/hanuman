import logging
import sys
from pathlib import Path
from typing import Any, Callable, MutableMapping

import structlog
from structlog.contextvars import merge_contextvars
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer, TimeStamper

Processor = Callable[[Any, str, MutableMapping[str, Any]], Any]

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class LevelFilter(logging.Filter):
    def __init__(self, level: int) -> None:
        super().__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self.level


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO

    processors: list[Processor] = [
        merge_contextvars,
        structlog.processors.add_log_level,
        TimeStamper(fmt="iso"),
    ]

    renderer: Processor = ConsoleRenderer() if debug else JSONRenderer()
    processors.append(renderer)

    info_file_handler = logging.FileHandler(
        LOG_DIR / "hanuman_info.json", mode="a", encoding="utf-8"
    )
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.addFilter(LevelFilter(logging.INFO))

    debug_file_handler = logging.FileHandler(
        LOG_DIR / "hanuman_debug.json", mode="a", encoding="utf-8"
    )
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.addFilter(LevelFilter(logging.DEBUG))

    error_file_handler = logging.FileHandler(
        LOG_DIR / "hanuman_error.json", mode="a", encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.addFilter(LevelFilter(logging.ERROR))

    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            debug_file_handler,
            info_file_handler,
            error_file_handler,
        ],
        force=True,
    )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name or "hanuman")
