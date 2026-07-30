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
    manifest: ConnectorManifest
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
                Path(f"src/hanuman/services/connectors/{python_name}.py"),
                _connector_template(manifest),
            ),
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
        return ScaffoldPlan(
            connector_id=manifest.id,
            manifest=manifest,
            files=files,
        )

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

        integration_paths = (
            self.project_root / _REGISTRY_PATH,
            self.project_root / _REGISTRY_TEST_PATH,
            self.project_root / _API_PATH,
            self.project_root / _FRONTEND_PATH,
            self.project_root / _CONSTELLATION_PATH,
        )
    
        integration_before = {path: path.read_bytes() for path in integration_paths}

        written: list[Path] = []
        previous_contents: dict[Path, bytes | None] = {}

        try:
            for item in plan.files:
                destination = self.project_root / item.path
                previous_contents[destination] = (
                    destination.read_bytes() if destination.exists() else None
                )
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(item.content, encoding="utf-8")
                written.append(destination)

            update_registry(self.project_root, plan.manifest)
            update_registry_test(self.project_root, plan.manifest)
            update_api(self.project_root, plan.manifest)
            update_frontend(self.project_root, plan.manifest)
            update_constellation(self.project_root, plan.manifest)

        except (OSError, ValueError):
            for path, integration_previous in integration_before.items():
                path.write_bytes(integration_previous)

            for destination in reversed(written):
                previous = previous_contents[destination]
                if previous is None:
                    destination.unlink(missing_ok=True)
                else:
                    destination.write_bytes(previous)
            raise

        return tuple(written)


def _connector_template(manifest: ConnectorManifest) -> str:
    """Sélectionne le squelette technique adapté au type de connecteur."""

    renderers = {
        "remote_api": _remote_api_connector_template,
        "local_program": _local_program_connector_template,
        "local_filesystem": _local_filesystem_connector_template,
        "ai_provider": _ai_provider_connector_template,
    }

    return renderers[manifest.kind](manifest)


def _remote_api_connector_template(manifest: ConnectorManifest) -> str:
    class_name = f"{_pascal_case(manifest.id)}Connector"

    return f'''from __future__ import annotations


class {class_name}:
    """Adaptateur HTTP initial du connecteur {manifest.label}."""

    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def healthcheck(self) -> bool:
        """Vérifie minimalement que le connecteur est configuré."""

        return bool(self.base_url)
'''


def _local_program_connector_template(manifest: ConnectorManifest) -> str:
    class_name = f"{_pascal_case(manifest.id)}Connector"

    return f'''from __future__ import annotations

from pathlib import Path


class {class_name}:
    """Adaptateur initial du programme local {manifest.label}."""

    def __init__(self, executable: Path) -> None:
        self.executable = executable

    def healthcheck(self) -> bool:
        """Vérifie que l'exécutable local existe."""

        return self.executable.is_file()
'''


def _local_filesystem_connector_template(
    manifest: ConnectorManifest,
) -> str:
    class_name = f"{_pascal_case(manifest.id)}Connector"

    return f'''from __future__ import annotations

from pathlib import Path


class {class_name}:
    """Adaptateur initial du système de fichiers {manifest.label}."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def healthcheck(self) -> bool:
        """Vérifie que la racine locale existe."""

        return self.root.is_dir()
'''


def _ai_provider_connector_template(manifest: ConnectorManifest) -> str:
    class_name = f"{_pascal_case(manifest.id)}Connector"

    return f'''from __future__ import annotations


class {class_name}:
    """Adaptateur initial du fournisseur IA {manifest.label}."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def healthcheck(self) -> bool:
        """Vérifie que les paramètres minimaux sont présents."""

        return bool(self.api_key and self.model)
'''


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
_REGISTRY_TEST_PATH = Path("tests/services/test_connectors_registry.py")
_REGISTRY_TEST_START = "        # scaffold:connector-ids:start"
_REGISTRY_TEST_END = "        # scaffold:connector-ids:end"

def update_registry(
    project_root: Path,
    manifest: ConnectorManifest,
) -> bool:
    """Ajoute le connecteur à la zone générée du registre.

    Retourne True si le fichier a été modifié, False si le connecteur était
    déjà présent.
    """

    return _update_between_markers(
        project_root,
        relative_path=_REGISTRY_PATH,
        start_marker=_REGISTRY_START,
        end_marker=_REGISTRY_END,
        content=render_registry_descriptor(manifest),
    )

def render_registry_test_id(manifest: ConnectorManifest) -> str:
    """Rend l’identifiant attendu dans le test exhaustif du registre."""

    return f'        "{manifest.id}",'


def update_registry_test(
    project_root: Path,
    manifest: ConnectorManifest,
) -> bool:
    """Ajoute l’identifiant du connecteur au test exhaustif du registre."""

    return _update_between_markers(
        project_root,
        relative_path=_REGISTRY_TEST_PATH,
        start_marker=_REGISTRY_TEST_START,
        end_marker=_REGISTRY_TEST_END,
        content=render_registry_test_id(manifest),
    )

_API_PATH = Path("src/hanuman/api/routers/resources.py")
_API_START = "# scaffold:connector-routes:start"
_API_END = "# scaffold:connector-routes:end"

_FRONTEND_PATH = Path("frontend/src/models/connectors.ts")
_FRONTEND_START = "// scaffold:connector-definitions:start"
_FRONTEND_END = "// scaffold:connector-definitions:end"

_CONSTELLATION_PATH = Path("frontend/src/constellation/constellationModel.ts")
_CONSTELLATION_START = "// scaffold:visual-metadata:start"
_CONSTELLATION_END = "// scaffold:visual-metadata:end"


def _update_between_markers(
    project_root: Path,
    relative_path: Path,
    start_marker: str,
    end_marker: str,
    content: str,
) -> bool:
    """Insère un contenu généré entre deux marqueurs d'un fichier."""

    from hanuman.scaffold.markers import append_between_markers

    target_path = project_root.resolve() / relative_path
    source = target_path.read_text(encoding="utf-8")

    updated = append_between_markers(
        source,
        start_marker=start_marker,
        end_marker=end_marker,
        content=content,
    )

    if updated == source:
        return False

    target_path.write_text(updated, encoding="utf-8")
    return True


def render_api_status_route(manifest: ConnectorManifest) -> str:
    """Rend la route de statut FastAPI du connecteur."""

    python_name = manifest.id.replace("-", "_")

    return f'''@router.get("/{manifest.id}/status")
def {python_name}_status() -> dict[str, object]:
    from hanuman.services.core.{python_name}_service import ping_{python_name}

    status = ping_{python_name}()
    return {{
        "ok": status.ok,
        "configured": status.configured,
        "message": status.message,
    }}'''


def update_api(
    project_root: Path,
    manifest: ConnectorManifest,
) -> bool:
    """Ajoute la route de statut dans le routeur Resources."""

    return _update_between_markers(
        project_root,
        relative_path=_API_PATH,
        start_marker=_API_START,
        end_marker=_API_END,
        content=render_api_status_route(manifest),
    )


def _update_frontend_icon_import(
    project_root: Path,
    manifest: ConnectorManifest,
) -> bool:
    """Ajoute et trie l’icône dans l’import lucide-react."""

    target_path = project_root.resolve() / _FRONTEND_PATH
    source = target_path.read_text(encoding="utf-8")

    import_start = "import {\n"
    import_end = "} from 'lucide-react'"

    if source.count(import_start) != 1 or source.count(import_end) != 1:
        raise ValueError(
            "Le fichier frontend doit contenir exactement un import nommé "
            "depuis lucide-react."
        )

    body_start = source.index(import_start) + len(import_start)
    body_end = source.index(import_end, body_start)
    import_body = source[body_start:body_end]

    imported_icons = {
        line.strip().removesuffix(",")
        for line in import_body.splitlines()
        if line.strip()
    }

    icon = manifest.frontend.icon

    if icon in imported_icons:
        return False

    imported_icons.add(icon)

    sorted_import_body = "".join(
        f"  {imported_icon},\n"
        for imported_icon in sorted(imported_icons, key=str.casefold)
    )

    updated = source[:body_start] + sorted_import_body + source[body_end:]
    target_path.write_text(updated, encoding="utf-8")

    return True


def update_frontend(
    project_root: Path,
    manifest: ConnectorManifest,
) -> bool:
    """Ajoute l’icône et la définition du connecteur au catalogue frontend."""

    icon_changed = _update_frontend_icon_import(project_root, manifest)

    definition_changed = _update_between_markers(
        project_root,
        relative_path=_FRONTEND_PATH,
        start_marker=_FRONTEND_START,
        end_marker=_FRONTEND_END,
        content=render_frontend_connector(manifest),
    )

    return icon_changed or definition_changed

def update_constellation(
    project_root: Path,
    manifest: ConnectorManifest,
) -> bool:
    """Ajoute les métadonnées du connecteur à la constellation frontend."""

    return _update_between_markers(
        project_root,
        relative_path=_CONSTELLATION_PATH,
        start_marker=_CONSTELLATION_START,
        end_marker=_CONSTELLATION_END,
        content=render_constellation_metadata(manifest),
    )


_FRONTEND_KIND = {
    "remote_api": "external",
    "local_program": "local",
    "local_filesystem": "local",
    "ai_provider": "external",
}


def _typescript_string(value: str) -> str:
    """Échappe une valeur destinée à une chaîne TypeScript simple."""

    return value.replace("\\", "\\\\").replace("'", "\\'")


def render_frontend_connector(manifest: ConnectorManifest) -> str:
    """Rend la définition visuelle normalisée d'un connecteur."""

    connector_id = _typescript_string(manifest.id)
    label = _typescript_string(manifest.label)
    description = _typescript_string(manifest.description)
    frontend_kind = _FRONTEND_KIND[manifest.kind]
    status = _typescript_string(manifest.frontend.status)
    route = _typescript_string(manifest.frontend.route or f"/connectors?source={manifest.id}")
    icon = manifest.frontend.icon

    return (
        "  { "
        f"id: '{connector_id}', "
        f"label: '{label}', "
        f"description: '{description}', "
        f"kind: '{frontend_kind}', "
        f"status: '{status}', "
        f"route: '{route}', "
        f"icon: {icon}, "
        "},"
    )


def render_constellation_metadata(manifest: ConnectorManifest) -> str:
    """Rend les métadonnées visuelles de la constellation."""

    connector_id = _typescript_string(manifest.id)
    constellation = manifest.frontend.constellation

    return (
        f"  '{connector_id}': {{ "
        f"x: {constellation.x}, "
        f"y: {constellation.y}, "
        f"size: '{constellation.size}', "
        f"palette: '{constellation.palette}', "
        f"family: '{constellation.family}', "
        f"healthEndpoint: '/resources/{connector_id}/status', "
        "},"
    )
