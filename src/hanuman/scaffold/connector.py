from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hanuman.scaffold.manifest import ConnectorManifest


@dataclass(frozen=True, slots=True)
class PlannedFile:
    path: Path
    content: str


@dataclass(frozen=True, slots=True)
class ScaffoldPlan:
    connector_id: str
    files: tuple[PlannedFile, ...]

    @property
    def paths(self) -> tuple[Path, ...]:
        return tuple(item.path for item in self.files)


class ConnectorScaffold:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def plan(self, manifest: ConnectorManifest) -> ScaffoldPlan:
        python_name = manifest.id.replace("-", "_")
        files = (
            PlannedFile(
                Path(f"src/hanuman/services/core/{python_name}_service.py"),
                _service_template(manifest),
            ),
            PlannedFile(
                Path(f"tests/services/test_{python_name}_service.py"),
                _service_test_template(manifest),
            ),
            PlannedFile(
                Path(f"docs/connectors/{manifest.id}.md"),
                _documentation_template(manifest),
            ),
        )
        return ScaffoldPlan(connector_id=manifest.id, files=files)

    def validate(self, plan: ScaffoldPlan, *, force: bool = False) -> None:
        collisions = [item.path for item in plan.files if (self.project_root / item.path).exists()]
        if collisions and not force:
            rendered = ", ".join(str(path) for path in collisions)
            raise FileExistsError(
                f"Le scaffold refuse d'écraser des fichiers existants : {rendered}. "
                "Utiliser --force pour confirmer."
            )

    def apply(self, plan: ScaffoldPlan, *, force: bool = False) -> tuple[Path, ...]:
        self.validate(plan, force=force)
        written: list[Path] = []
        try:
            for item in plan.files:
                destination = self.project_root / item.path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(item.content, encoding="utf-8")
                written.append(destination)
        except OSError:
            for destination in reversed(written):
                destination.unlink(missing_ok=True)
            raise
        return tuple(written)


def _service_template(manifest: ConnectorManifest) -> str:
    class_name = _pascal_case(manifest.id)
    return f'''from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class {class_name}Status:
    ok: bool
    configured: bool
    message: str | None = None


def ping_{manifest.id.replace("-", "_")}() -> {class_name}Status:
    """Retourne l'état minimal du connecteur {manifest.label}."""

    return {class_name}Status(
        ok=True,
        configured=True,
        message=None,
    )
'''


def _service_test_template(manifest: ConnectorManifest) -> str:
    python_name = manifest.id.replace("-", "_")
    return f'''from __future__ import annotations

from hanuman.services.core.{python_name}_service import ping_{python_name}


def test_ping_{python_name}_returns_available_status() -> None:
    status = ping_{python_name}()

    assert status.ok is True
    assert status.configured is True
    assert status.message is None
'''


def _documentation_template(manifest: ConnectorManifest) -> str:
    capabilities = "\n".join(f"- `{item}`" for item in manifest.capabilities)
    return f'''# Connecteur {manifest.label}

## Statut

Structure initiale générée automatiquement. L'implémentation métier reste à compléter.

## Description

{manifest.description}

## Métadonnées

- Identifiant : `{manifest.id}`
- Type : `{manifest.kind}`
- Authentification requise : `{str(manifest.requires_auth).lower()}`
- Écriture autorisée : `{str(manifest.writable).lower()}`
- Profil de workspace : `{manifest.workspace}`

## Capacités

{capabilities}

## Intégration attendue

```text
Service
→ API
→ Registre
→ Frontend
→ Workspace
→ Constellation
→ Tests
```
'''


def _pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in value.replace("_", "-").split("-"))


_KIND_TO_PYTHON = {
    "remote_api": "ConnectorKind.REMOTE_API",
    "local_program": "ConnectorKind.LOCAL_PROGRAM",
    "local_filesystem": "ConnectorKind.LOCAL_FILESYSTEM",
    "ai_provider": "ConnectorKind.AI_PROVIDER",
}


def render_registry_descriptor(manifest: ConnectorManifest) -> str:
    """Rend la déclaration Python d'un connecteur pour le registre."""

    capabilities = "\n".join(f'            "{capability}",' for capability in manifest.capabilities)

    optional_arguments: list[str] = []
    if manifest.writable:
        optional_arguments.append("        writable=True,")
    if manifest.requires_auth:
        optional_arguments.append("        requires_auth=True,")

    optional_block = ""
    if optional_arguments:
        optional_block = "\n" + "\n".join(optional_arguments)

    return f'''    ConnectorDescriptor(
        id="{manifest.id}",
        label="{manifest.label}",
        description="{manifest.description}",
        kind={_KIND_TO_PYTHON[manifest.kind]},
        capabilities=[
{capabilities}
        ],{optional_block}
        status_endpoint="/resources/{manifest.id}/status",
    ),'''


_REGISTRY_PATH = Path("src/hanuman/services/connectors_registry.py")
_REGISTRY_START = "# scaffold:connectors:start"
_REGISTRY_END = "# scaffold:connectors:end"


def update_registry(
    project_root: Path,
    manifest: ConnectorManifest,
) -> bool:
    """Ajoute le connecteur à la zone générée du registre.

    Retourne True si le fichier a été modifié, False si le connecteur était
    déjà présent.
    """

    from hanuman.scaffold.markers import append_between_markers

    registry_path = project_root.resolve() / _REGISTRY_PATH
    source = registry_path.read_text(encoding="utf-8")

    updated = append_between_markers(
        source,
        start_marker=_REGISTRY_START,
        end_marker=_REGISTRY_END,
        content=render_registry_descriptor(manifest),
    )

    if updated == source:
        return False

    registry_path.write_text(updated, encoding="utf-8")
    return True
