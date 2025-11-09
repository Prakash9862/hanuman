import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Callable, MutableMapping

import structlog
from structlog.contextvars import merge_contextvars
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer, TimeStamper
from structlog.stdlib import ProcessorFormatter

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

    common_processors: list[Processor] = [
        merge_contextvars,
        structlog.processors.add_log_level,
        TimeStamper(fmt="iso"),
    ]

    console_formatter = ProcessorFormatter(
        processor=ConsoleRenderer(),
        foreign_pre_chain=common_processors,
    )

    json_formatter = ProcessorFormatter(
        processor=JSONRenderer(),
        foreign_pre_chain=common_processors,
    )

    info_file_handler = TimedRotatingFileHandler(
        LOG_DIR / "hanuman_info.json",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.addFilter(LevelFilter(logging.INFO))
    info_file_handler.setFormatter(json_formatter)

    debug_file_handler = TimedRotatingFileHandler(
        LOG_DIR / "hanuman_debug.json",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.addFilter(LevelFilter(logging.DEBUG))
    debug_file_handler.setFormatter(json_formatter)

    error_file_handler = TimedRotatingFileHandler(
        LOG_DIR / "hanuman_error.json",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.addFilter(LevelFilter(logging.ERROR))
    error_file_handler.setFormatter(json_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[
            console_handler,
            debug_file_handler,
            info_file_handler,
            error_file_handler,
        ],
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    return structlog.get_logger(name or "hanuman")
