# src/hanuman/core/logging.py

import logging
import logging.config
from logging import Logger
from pathlib import Path

import yaml


def setup_logging(level: int = logging.INFO) -> Logger:
    """
    Initialise le système de logs à partir du fichier config/logging.yaml.
    Utilise dictConfig pour charger : handlers, formatters, loggers.

    :param level: Niveau par défaut utilisé en cas d'échec
    :return: Logger nommé "hanuman"
    """

    config_path = Path(__file__).resolve().parents[3] / "config" / "logging.yaml"
    print(f"[DEBUG] Chargement config log depuis : {config_path}")  # temporaire

    if config_path.exists():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logging.config.dictConfig(config)
        except Exception as e:
            print(f"⚠️ Échec du chargement logging.yaml : {e}")
            logging.basicConfig(level=level)
    else:
        print("⚠️ logging.yaml introuvable, fallback basicConfig.")
        logging.basicConfig(level=level)

    return logging.getLogger("hanuman")
