from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

THEME_NAME = "hanuman-chess"


def _vault_root() -> Path:
    configured = os.environ.get("OBSIDIAN_VAULT_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path("/home/vince/Prakash/projets/Obsidian_Priv-").expanduser().resolve()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def install() -> dict[str, str]:
    vault = _vault_root()
    source = _project_root() / "assets" / "obsidian" / f"{THEME_NAME}.css"
    if not source.exists():
        raise FileNotFoundError(f"Snippet source introuvable : {source}")
    if not vault.exists():
        raise FileNotFoundError(f"Vault Obsidian introuvable : {vault}")

    obsidian_dir = vault / ".obsidian"
    snippets_dir = obsidian_dir / "snippets"
    snippets_dir.mkdir(parents=True, exist_ok=True)

    destination = snippets_dir / source.name
    shutil.copy2(source, destination)

    appearance_path = obsidian_dir / "appearance.json"
    appearance = _read_json(appearance_path)
    enabled = appearance.get("enabledCssSnippets", [])
    if not isinstance(enabled, list):
        enabled = []
    enabled_names = [str(item) for item in enabled]
    if THEME_NAME not in enabled_names:
        enabled_names.append(THEME_NAME)
    appearance["enabledCssSnippets"] = enabled_names
    appearance_path.write_text(
        json.dumps(appearance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "status": "ok",
        "vault": str(vault),
        "snippet": str(destination),
        "appearance": str(appearance_path),
        "enabled": THEME_NAME,
    }


if __name__ == "__main__":
    print(install())
