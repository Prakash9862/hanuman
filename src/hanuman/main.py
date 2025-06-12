from core.logging import setup_logging

logger = setup_logging()

logger.debug("🐍 DEBUG message triggered")
logger.info("📘 INFO message triggered")
logger.warning("⚠️ WARNING message triggered")
logger.error("💥 ERROR message triggered")
