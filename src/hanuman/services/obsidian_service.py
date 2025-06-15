from pathlib import Path

from hanuman.utils.decorators import safe_ping

VAULT_PATH = Path("/home/prakash/Prakash/obsidian/Privé")


@safe_ping("obsidian")
def ping_obsidian() -> dict:
    if not VAULT_PATH.exists() or not VAULT_PATH.is_dir():
        raise FileNotFoundError(f"Vault introuvable : {VAULT_PATH}")

    return {
        "path": str(VAULT_PATH),
        "note_count": len(list(VAULT_PATH.glob("*.md"))),
    }
