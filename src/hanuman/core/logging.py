# src/hanuman/core/logging.py

import logging
import logging.config
from logging import Logger
from pathlib import Path
from typing import Optional

import yaml


def setup_logging(
    config_path: Optional[Path] = None,
    default_level: int = logging.INFO,
    env: str = "default",
) -> Logger:
    """
    Initialise le système de log à partir du fichier YAML.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parents[2] / "config" / "logging.yaml"

    if config_path.exists():
        try:
            with config_path.open("r") as f:
                config = yaml.safe_load(f)
                logging.config.dictConfig(config)
        except Exception as e:
            print(f"⚠️ Failed to load logging config: {e}")
            logging.basicConfig(level=default_level)
    else:
        print("⚠️ Logging config not found, using basicConfig.")
        logging.basicConfig(level=default_level)

    return logging.getLogger("hanuman")
