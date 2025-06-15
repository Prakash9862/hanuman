# src/hanuman/services/obsidian_service.py

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

VAULT_PATH = Path("/home/prakash/Prakash/obsidian/Privé")


def ping_obsidian() -> dict:
    if VAULT_PATH.exists() and VAULT_PATH.is_dir():
        logger.info("🗃️ Vault Obsidian détecté")
        return {
            "ok": True,
            "path": str(VAULT_PATH),
            "note_count": len(list(VAULT_PATH.glob("*.md"))),
        }
    else:
        logger.warning("⚠️ Vault Obsidian introuvable")
        return {"ok": False, "error": f"Vault introuvable : {VAULT_PATH}"}
