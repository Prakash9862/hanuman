# src/hanuman/core/token_manager.py

import json
from pathlib import Path
from typing import Any, Dict, cast

TOKEN_DIR = Path("secrets")
TOKEN_DIR.mkdir(exist_ok=True)


def save_token_json(service: str, data: Dict[str, Any]) -> None:
    """
    Sauvegarde les données d'authentification dans un fichier JSON localisé dans 'secrets/'.

    Args:
        service: Nom du service (utilisé comme préfixe du fichier)
        data: Données à sauvegarder (dictionnaire JSON)
    """
    filepath = TOKEN_DIR / f"{service}_token.json"
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_token_json(service: str) -> Dict[str, Any]:
    """
    Charge les données d'authentification à partir d'un fichier JSON localisé dans 'secrets/'.

    Args:
        service: Nom du service (correspondant au fichier)

    Returns:
        Un dictionnaire de données JSON, vide si le fichier n'existe pas.
    """
    filepath = TOKEN_DIR / f"{service}_token.json"
    if not filepath.exists():
        return {}
    with filepath.open(encoding="utf-8") as f:
        return cast(Dict[str, Any], json.load(f))
