from __future__ import annotations

import re
from dataclasses import dataclass, field
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
_ALLOWED_FRONTEND_STATUSES = {"available", "partial", "planned"}
_ALLOWED_CONSTELLATION_SIZES = {"dwarf", "small", "medium", "large", "giant"}
_ALLOWED_CONSTELLATION_FAMILIES = {
    "terrestrial",
    "gas",
    "ice",
    "oceanic",
    "crystalline",
    "desert",
    "metallic",
    "volcanic",
    "forest",
}


@dataclass(frozen=True, slots=True)
class ConstellationManifest:
    x: int = 50
    y: int = 50
    size: str = "small"
    palette: str = "graphite"
    family: str = "metallic"


@dataclass(frozen=True, slots=True)
class FrontendManifest:
    icon: str = "Layers3"
    status: str = "planned"
    route: str | None = None
    constellation: ConstellationManifest = field(default_factory=ConstellationManifest)


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
    frontend: FrontendManifest = field(default_factory=FrontendManifest)

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
                raise ValueError(
                    f"Capacité invalide : {normalized}. Format attendu : domaine.action."
                )
            capabilities.append(normalized)

        if len(set(capabilities)) != len(capabilities):
            raise ValueError("Le manifeste contient des capacités dupliquées.")

        frontend = _frontend_manifest(
            raw.get("frontend"),
            connector_id=connector_id,
        )

        return cls(
            id=connector_id,
            label=_required_string(raw, "label").strip(),
            description=_required_string(raw, "description").strip(),
            kind=kind,
            capabilities=tuple(capabilities),
            requires_auth=_optional_bool(raw, "requires_auth", default=False),
            writable=_optional_bool(raw, "writable", default=False),
            workspace=workspace,
            frontend=frontend,
        )


def _frontend_manifest(
    raw: Any,
    *,
    connector_id: str,
) -> FrontendManifest:
    if raw is None:
        return FrontendManifest(
            route=f"/connectors?source={connector_id}",
        )

    if not isinstance(raw, dict):
        raise ValueError("Le champ frontend doit contenir un objet.")

    icon = _optional_string(raw, "icon", default="Layers3")

    status = _optional_string(raw, "status", default="planned").lower()
    if status not in _ALLOWED_FRONTEND_STATUSES:
        choices = ", ".join(sorted(_ALLOWED_FRONTEND_STATUSES))
        raise ValueError(f"Statut frontend invalide : {status}. Valeurs : {choices}.")

    route = _optional_string(
        raw,
        "route",
        default=f"/connectors?source={connector_id}",
    )
    if not route.startswith("/"):
        raise ValueError("La route frontend doit commencer par '/'.")

    constellation = _constellation_manifest(raw.get("constellation"))

    return FrontendManifest(
        icon=icon,
        status=status,
        route=route,
        constellation=constellation,
    )


def _constellation_manifest(raw: Any) -> ConstellationManifest:
    if raw is None:
        return ConstellationManifest()

    if not isinstance(raw, dict):
        raise ValueError("Le champ frontend.constellation doit contenir un objet.")

    x = _coordinate(raw, "x", default=50)
    y = _coordinate(raw, "y", default=50)

    size = _optional_string(raw, "size", default="small").lower()
    if size not in _ALLOWED_CONSTELLATION_SIZES:
        choices = ", ".join(sorted(_ALLOWED_CONSTELLATION_SIZES))
        raise ValueError(f"Taille de constellation invalide : {size}. Valeurs : {choices}.")

    family = _optional_string(raw, "family", default="metallic").lower()
    if family not in _ALLOWED_CONSTELLATION_FAMILIES:
        choices = ", ".join(sorted(_ALLOWED_CONSTELLATION_FAMILIES))
        raise ValueError(f"Famille de constellation invalide : {family}. Valeurs : {choices}.")

    palette = _optional_string(raw, "palette", default="graphite").lower()

    return ConstellationManifest(
        x=x,
        y=y,
        size=size,
        palette=palette,
        family=family,
    )


def _coordinate(raw: dict[str, Any], key: str, *, default: int) -> int:
    value: object = raw.get(key)

    if value is None:
        return default

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Le champ frontend.constellation.{key} doit être un entier.")

    if not 0 <= value <= 100:
        raise ValueError(
            f"Le champ frontend.constellation.{key} " "doit être compris entre 0 et 100."
        )

    return value


def _optional_string(
    raw: dict[str, Any],
    key: str,
    *,
    default: str,
) -> str:
    value: object = raw.get(key)

    if value is None:
        return default

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Le champ {key} doit être une chaîne non vide.")

    return value.strip()


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
