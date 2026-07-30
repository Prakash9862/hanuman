from __future__ import annotations

from pathlib import Path

import pytest

from hanuman.scaffold.connector import ConnectorScaffold
from hanuman.scaffold.manifest import ConnectorManifest, load_connector_manifest


def _manifest() -> ConnectorManifest:
    return ConnectorManifest.from_mapping(
        {
            "id": "devdocs",
            "label": "DevDocs",
            "description": "Documentation technique.",
            "kind": "remote_api",
            "capabilities": ["documentation.search", "documentation.open"],
            "workspace": "search",
        }
    )


def test_manifest_normalizes_values() -> None:
    manifest = ConnectorManifest.from_mapping(
        {
            "id": " DevDocs ",
            "label": "DevDocs",
            "description": "Documentation technique.",
            "kind": "REMOTE_API",
            "capabilities": ["Documentation.Search"],
        }
    )

    assert manifest.id == "devdocs"
    assert manifest.kind == "remote_api"
    assert manifest.capabilities == ("documentation.search",)
    assert manifest.workspace == "catalog-only"


def test_manifest_rejects_invalid_connector_id() -> None:
    with pytest.raises(ValueError, match="identifiant"):
        ConnectorManifest.from_mapping(
            {
                "id": "Dev Docs",
                "label": "DevDocs",
                "description": "Documentation technique.",
                "kind": "remote_api",
                "capabilities": ["documentation.search"],
            }
        )


def test_load_connector_manifest(tmp_path: Path) -> None:
    path = tmp_path / "devdocs.yaml"
    path.write_text(
        """id: devdocs
label: DevDocs
description: Documentation technique.
kind: remote_api
capabilities:
  - documentation.search
""",
        encoding="utf-8",
    )

    assert load_connector_manifest(path).id == "devdocs"


def test_plan_is_deterministic(tmp_path: Path) -> None:
    scaffold = ConnectorScaffold(tmp_path)

    first = scaffold.plan(_manifest())
    second = scaffold.plan(_manifest())

    assert first == second
    assert first.paths == (
        Path("src/hanuman/services/core/devdocs_service.py"),
        Path("tests/services/test_devdocs_service.py"),
        Path("docs/connectors/devdocs.md"),
    )


def test_apply_creates_planned_files_and_updates_registry(tmp_path: Path) -> None:
    registry = tmp_path / "src/hanuman/services/connectors_registry.py"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        """_CONNECTORS = (
    # scaffold:connectors:start

    # scaffold:connectors:end
)
""",
        encoding="utf-8",
    )

    scaffold = ConnectorScaffold(tmp_path)
    plan = scaffold.plan(_manifest())

    written = scaffold.apply(plan)

    assert len(written) == 3
    assert all(path.exists() for path in written)
    assert "ping_devdocs" in written[0].read_text(encoding="utf-8")

    registry_content = registry.read_text(encoding="utf-8")
    assert 'id="devdocs"' in registry_content
    assert 'status_endpoint="/resources/devdocs/status"' in registry_content


def test_apply_refuses_existing_files(tmp_path: Path) -> None:
    scaffold = ConnectorScaffold(tmp_path)
    plan = scaffold.plan(_manifest())
    target = tmp_path / plan.files[0].path
    target.parent.mkdir(parents=True)
    target.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="--force"):
        scaffold.apply(plan)

    assert target.read_text(encoding="utf-8") == "existing"


def test_render_registry_descriptor_contains_manifest_metadata() -> None:
    from hanuman.scaffold.connector import render_registry_descriptor

    manifest = ConnectorManifest(
        id="devdocs",
        label="DevDocs",
        description="Recherche de documentation technique.",
        kind="remote_api",
        capabilities=(
            "documentation.search",
            "documentation.read",
        ),
        workspace="search",
    )

    rendered = render_registry_descriptor(manifest)

    assert 'id="devdocs"' in rendered
    assert 'label="DevDocs"' in rendered
    assert 'description="Recherche de documentation technique."' in rendered
    assert "kind=ConnectorKind.REMOTE_API" in rendered
    assert '"documentation.search"' in rendered
    assert '"documentation.read"' in rendered
    assert 'status_endpoint="/resources/devdocs/status"' in rendered
    assert "requires_auth=True" not in rendered
    assert "writable=True" not in rendered


def test_render_registry_descriptor_adds_optional_flags() -> None:
    from hanuman.scaffold.connector import render_registry_descriptor

    manifest = ConnectorManifest(
        id="example",
        label="Example",
        description="Connecteur de test.",
        kind="local_program",
        capabilities=("example.read",),
        requires_auth=True,
        writable=True,
    )

    rendered = render_registry_descriptor(manifest)

    assert "kind=ConnectorKind.LOCAL_PROGRAM" in rendered
    assert "requires_auth=True" in rendered
    assert "writable=True" in rendered


def test_update_registry_inserts_descriptor_without_touching_manual_entries(
    tmp_path,
) -> None:
    from hanuman.scaffold.connector import update_registry

    registry = tmp_path / "src/hanuman/services/connectors_registry.py"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        """_CONNECTORS = (
    ConnectorDescriptor(id="manual"),
    # scaffold:connectors:start

    # scaffold:connectors:end
)
""",
        encoding="utf-8",
    )

    manifest = ConnectorManifest(
        id="example",
        label="Example",
        description="Connecteur de test.",
        kind="remote_api",
        capabilities=("example.read",),
    )

    changed = update_registry(tmp_path, manifest)
    rendered = registry.read_text(encoding="utf-8")

    assert changed is True
    assert 'ConnectorDescriptor(id="manual")' in rendered
    assert 'id="example"' in rendered
    assert 'status_endpoint="/resources/example/status"' in rendered


def test_update_registry_is_idempotent(tmp_path) -> None:
    from hanuman.scaffold.connector import update_registry

    registry = tmp_path / "src/hanuman/services/connectors_registry.py"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        """_CONNECTORS = (
    # scaffold:connectors:start

    # scaffold:connectors:end
)
""",
        encoding="utf-8",
    )

    manifest = ConnectorManifest(
        id="example",
        label="Example",
        description="Connecteur de test.",
        kind="remote_api",
        capabilities=("example.read",),
    )

    assert update_registry(tmp_path, manifest) is True
    first = registry.read_text(encoding="utf-8")

    assert update_registry(tmp_path, manifest) is False
    second = registry.read_text(encoding="utf-8")

    assert second == first
    assert second.count('id="example"') == 1


def test_render_api_status_route_uses_generated_service() -> None:
    from hanuman.scaffold.connector import render_api_status_route

    rendered = render_api_status_route(_manifest())

    assert '@router.get("/devdocs/status")' in rendered
    assert "def devdocs_status()" in rendered
    assert "from hanuman.services.core.devdocs_service import ping_devdocs" in rendered
    assert "status = ping_devdocs()" in rendered
    assert '"configured": status.configured' in rendered


def test_update_api_inserts_route_and_preserves_manual_routes(tmp_path: Path) -> None:
    from hanuman.scaffold.connector import update_api

    api = tmp_path / "src/hanuman/api/routers/resources.py"
    api.parent.mkdir(parents=True)
    api.write_text(
        '''router = APIRouter(prefix="/resources")

@router.get("/manual/status")
def manual_status():
    return {"ok": True}


# scaffold:connector-routes:start

# scaffold:connector-routes:end
''',
        encoding="utf-8",
    )

    changed = update_api(tmp_path, _manifest())
    rendered = api.read_text(encoding="utf-8")

    assert changed is True
    assert '@router.get("/manual/status")' in rendered
    assert '@router.get("/devdocs/status")' in rendered
    assert "def devdocs_status()" in rendered


def test_update_api_is_idempotent(tmp_path: Path) -> None:
    from hanuman.scaffold.connector import update_api

    api = tmp_path / "src/hanuman/api/routers/resources.py"
    api.parent.mkdir(parents=True)
    api.write_text(
        '''router = APIRouter(prefix="/resources")

# scaffold:connector-routes:start

# scaffold:connector-routes:end
''',
        encoding="utf-8",
    )

    assert update_api(tmp_path, _manifest()) is True
    first = api.read_text(encoding="utf-8")

    assert update_api(tmp_path, _manifest()) is False
    second = api.read_text(encoding="utf-8")

    assert second == first
    assert second.count('@router.get("/devdocs/status")') == 1


def test_render_frontend_connector_uses_safe_visual_defaults() -> None:
    from hanuman.scaffold.connector import render_frontend_connector

    rendered = render_frontend_connector(_manifest())

    assert "id: 'devdocs'" in rendered
    assert "label: 'DevDocs'" in rendered
    assert "description: 'Documentation technique.'" in rendered
    assert "kind: 'external'" in rendered
    assert "status: 'planned'" in rendered
    assert "route: '/connectors?source=devdocs'" in rendered
    assert "icon: Layers3" in rendered


def test_render_frontend_connector_maps_local_kinds() -> None:
    from hanuman.scaffold.connector import render_frontend_connector

    manifest = ConnectorManifest(
        id="local-docs",
        label="Local Docs",
        description="Documentation locale.",
        kind="local_filesystem",
        capabilities=("documentation.read",),
    )

    rendered = render_frontend_connector(manifest)

    assert "kind: 'local'" in rendered


def test_render_frontend_connector_escapes_typescript_strings() -> None:
    from hanuman.scaffold.connector import render_frontend_connector

    manifest = ConnectorManifest(
        id="example",
        label="L'exemple",
        description="Documentation d'un outil.",
        kind="remote_api",
        capabilities=("example.read",),
    )

    rendered = render_frontend_connector(manifest)

    assert "label: 'L\\'exemple'" in rendered
    assert "description: 'Documentation d\\'un outil.'" in rendered


def test_render_constellation_metadata_uses_neutral_defaults() -> None:
    from hanuman.scaffold.connector import render_constellation_metadata

    rendered = render_constellation_metadata(_manifest())

    assert "'devdocs': {" in rendered
    assert "x: 50" in rendered
    assert "y: 50" in rendered
    assert "size: 'small'" in rendered
    assert "palette: 'graphite'" in rendered
    assert "family: 'metallic'" in rendered
    assert "healthEndpoint: '/resources/devdocs/status'" in rendered


def test_manifest_parses_frontend_configuration() -> None:
    manifest = ConnectorManifest.from_mapping(
        {
            "id": "devdocs",
            "label": "DevDocs",
            "description": "Documentation technique.",
            "kind": "remote_api",
            "capabilities": ["documentation.search"],
            "frontend": {
                "icon": "BookOpen",
                "status": "partial",
                "route": "/connectors?source=devdocs",
                "constellation": {
                    "x": 61,
                    "y": 37,
                    "size": "medium",
                    "palette": "azure",
                    "family": "crystalline",
                },
            },
        }
    )

    assert manifest.frontend.icon == "BookOpen"
    assert manifest.frontend.status == "partial"
    assert manifest.frontend.route == "/connectors?source=devdocs"
    assert manifest.frontend.constellation.x == 61
    assert manifest.frontend.constellation.y == 37
    assert manifest.frontend.constellation.size == "medium"
    assert manifest.frontend.constellation.palette == "azure"
    assert manifest.frontend.constellation.family == "crystalline"


def test_manifest_adds_safe_frontend_defaults() -> None:
    manifest = _manifest()

    assert manifest.frontend.icon == "Layers3"
    assert manifest.frontend.status == "planned"
    assert manifest.frontend.route == "/connectors?source=devdocs"
    assert manifest.frontend.constellation.x == 50
    assert manifest.frontend.constellation.y == 50
    assert manifest.frontend.constellation.size == "small"
    assert manifest.frontend.constellation.palette == "graphite"
    assert manifest.frontend.constellation.family == "metallic"


@pytest.mark.parametrize(
    ("frontend", "message"),
    [
        ({"status": "broken"}, "Statut frontend invalide"),
        ({"route": "connectors/devdocs"}, "doit commencer"),
        (
            {"constellation": {"x": 101}},
            "doit être compris entre 0 et 100",
        ),
        (
            {"constellation": {"size": "enormous"}},
            "Taille de constellation invalide",
        ),
        (
            {"constellation": {"family": "digital"}},
            "Famille de constellation invalide",
        ),
    ],
)
def test_manifest_rejects_invalid_frontend_configuration(
    frontend: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ConnectorManifest.from_mapping(
            {
                "id": "devdocs",
                "label": "DevDocs",
                "description": "Documentation technique.",
                "kind": "remote_api",
                "capabilities": ["documentation.search"],
                "frontend": frontend,
            }
        )


def test_renderers_use_frontend_manifest_configuration() -> None:
    from hanuman.scaffold.connector import (
        render_constellation_metadata,
        render_frontend_connector,
    )

    manifest = ConnectorManifest.from_mapping(
        {
            "id": "devdocs",
            "label": "DevDocs",
            "description": "Documentation technique.",
            "kind": "remote_api",
            "capabilities": ["documentation.search"],
            "frontend": {
                "icon": "BookOpen",
                "status": "partial",
                "route": "/docs/devdocs",
                "constellation": {
                    "x": 61,
                    "y": 37,
                    "size": "medium",
                    "palette": "azure",
                    "family": "crystalline",
                },
            },
        }
    )

    frontend = render_frontend_connector(manifest)
    constellation = render_constellation_metadata(manifest)

    assert "status: 'partial'" in frontend
    assert "route: '/docs/devdocs'" in frontend
    assert "icon: BookOpen" in frontend

    assert "x: 61" in constellation
    assert "y: 37" in constellation
    assert "size: 'medium'" in constellation
    assert "palette: 'azure'" in constellation
    assert "family: 'crystalline'" in constellation
