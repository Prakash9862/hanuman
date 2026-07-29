from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_CONNECTOR_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_ALLOWED_KINDS = {
    "remote_api",
    "local_program",
    "local_filesystem",
    "ai_provider",
}
_ALLOWED_WORKSPACES = {"catalog-only", "search", "dashboard", "custom"}


@dataclass(frozen=True, slots=True)
class ConnectorManifest:
    id: str
    label: str
    description: str
    kind: str
    capabilities: tuple[str, ...]
    requires_auth: bool = False
    writable: bool = False
    workspace: str = "catalog-only"

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "ConnectorManifest":
        connector_id = _required_string(raw, "id").strip().lower()
        if not _CONNECTOR_ID_RE.fullmatch(connector_id):
            raise ValueError(
                "L'identifiant doit commencer par une lettre minuscule et ne contenir "
                "que des lettres minuscules, chiffres ou tirets."
            )

        kind = _required_string(raw, "kind").strip().lower()
        if kind not in _ALLOWED_KINDS:
            choices = ", ".join(sorted(_ALLOWED_KINDS))
            raise ValueError(f"Type de connecteur invalide : {kind}. Valeurs : {choices}.")

        workspace = str(raw.get("workspace", "catalog-only")).strip().lower()
        if workspace not in _ALLOWED_WORKSPACES:
            choices = ", ".join(sorted(_ALLOWED_WORKSPACES))
            raise ValueError(f"Profil de workspace invalide : {workspace}. Valeurs : {choices}.")

        raw_capabilities = raw.get("capabilities")
        if not isinstance(raw_capabilities, list) or not raw_capabilities:
            raise ValueError("Le manifeste doit déclarer au moins une capacité.")

        capabilities: list[str] = []
        for value in raw_capabilities:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Chaque capacité doit être une chaîne non vide.")
            normalized = value.strip().lower()
            if "." not in normalized:
                raise ValueError(f"Capacité invalide : {normalized}. Format attendu : domaine.action.")
            capabilities.append(normalized)

        if len(set(capabilities)) != len(capabilities):
            raise ValueError("Le manifeste contient des capacités dupliquées.")

        return cls(
            id=connector_id,
            label=_required_string(raw, "label").strip(),
            description=_required_string(raw, "description").strip(),
            kind=kind,
            capabilities=tuple(capabilities),
            requires_auth=_optional_bool(raw, "requires_auth", default=False),
            writable=_optional_bool(raw, "writable", default=False),
            workspace=workspace,
        )


def load_connector_manifest(path: Path) -> ConnectorManifest:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Impossible de lire le manifeste {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML invalide dans {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError("Le manifeste doit contenir un objet YAML à la racine.")
    return ConnectorManifest.from_mapping(raw)


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Champ obligatoire absent ou invalide : {key}.")
    return value


def _optional_bool(raw: dict[str, Any], key: str, *, default: bool) -> bool:
    value = raw.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"Le champ {key} doit être un booléen.")
    return value
