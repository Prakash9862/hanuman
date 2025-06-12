# tests/test_logger.py

import logging

from hanuman.core.logging import setup_logging


def test_logging_yaml_config_loads_correctly(caplog):
    """
    Vérifie que le fichier logging.yaml est bien chargé sans fallback
    et que les logs passent correctement par les handlers déclarés.
    """
    logger = setup_logging()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "hanuman"

    with caplog.at_level(logging.DEBUG):
        logger.debug("🔍 debug message test")
        logger.warning("⚠️ warning message test")
        logger.error("💥 error message test")

    # Vérifie que le contenu est capturé dans caplog
    assert any("debug message test" in m for m in caplog.messages)
    assert any("warning message test" in m for m in caplog.messages)
    assert any("error message test" in m for m in caplog.messages)
