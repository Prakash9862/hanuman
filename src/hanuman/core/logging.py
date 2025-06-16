import logging
import sys
from pathlib import Path
from typing import Optional

import structlog


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


# 📁 Création du dossier logs si inexistant
LOG_DIR = get_project_root() / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

DEBUG_LOG_PATH = LOG_DIR / "hanuman_debug.log"
ERROR_LOG_PATH = LOG_DIR / "hanuman_error.log"


def setup_logging(dev_mode: bool = True):
    """
    Configure structlog pour Hanuman.
    Active : console + fichier debug + fichier JSON d’erreurs.
    """
    # Base root logger
    logging.basicConfig(
        level=logging.DEBUG if dev_mode else logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )

    # Fichier debug texte
    debug_handler = logging.FileHandler(DEBUG_LOG_PATH, encoding="utf-8")
    debug_handler.setLevel(logging.DEBUG)

    # Fichier erreur JSON
    error_handler = logging.FileHandler(ERROR_LOG_PATH, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)

    root_logger = logging.getLogger()
    root_logger.addHandler(debug_handler)
    root_logger.addHandler(error_handler)

    # Structlog pipeline
    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.format_exc_info,
    ]

    if dev_mode:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger("hanuman")


def get_logger(name: Optional[str] = None):
    """Retourne un logger structlog contextualisable"""
    return structlog.get_logger(name or "hanuman")
