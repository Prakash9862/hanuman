from pathlib import Path

from hanuman.models.ping import PingResult  # ✅ Import modèle global
from hanuman.utils.decorators import trace_endpoint

VAULT_PATH = Path("/home/prakash/Prakash/obsidian/Privé")


@trace_endpoint("obsidian", catch=True)
def ping_obsidian() -> PingResult:
    if not VAULT_PATH.exists() or not VAULT_PATH.is_dir():
        raise FileNotFoundError(f"Vault introuvable : {VAULT_PATH}")

    return PingResult(
        ok=True,
        source="obsidian",
        detail={
            "path": str(VAULT_PATH),
            "note_count": len(list(VAULT_PATH.glob("*.md"))),
        },
    )
