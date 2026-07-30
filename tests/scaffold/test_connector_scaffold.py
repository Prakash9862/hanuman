from __future__ import annotations

from pathlib import Path

import pytest

from hanuman.scaffold.connector import (
    ConnectorScaffold,
    update_constellation,
    update_frontend,
)
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
        Path("src/hanuman/services/connectors/devdocs.py"),
        Path("src/hanuman/services/core/devdocs_service.py"),
        Path("tests/services/test_devdocs_service.py"),
        Path("docs/connectors/devdocs.md"),
    )


def test_apply_creates_planned_files_and_updates_integrations(
    tmp_path: Path,
) -> None:
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

    registry_test = tmp_path / "tests/services/test_connectors_registry.py"
    registry_test.parent.mkdir(parents=True)
    registry_test.write_text(
        """def test_registry_contains_existing_connectors() -> None:
    assert {
        # scaffold:connector-ids:start
        # scaffold:connector-ids:end
    }
""",
        encoding="utf-8",
    )

    api = tmp_path / "src/hanuman/api/routers/resources.py"
    api.parent.mkdir(parents=True)
    api.write_text(
        '''router = APIRouter(prefix="/resources")

# scaffold:connector-routes:start

# scaffold:connector-routes:end
''',
        encoding="utf-8",
    )

    frontend = tmp_path / "frontend/src/models/connectors.ts"
    frontend.parent.mkdir(parents=True)
    frontend.write_text(
        """import {
  BookOpen,
} from 'lucide-react'

const CONNECTORS = [
  // scaffold:connector-definitions:start
  // scaffold:connector-definitions:end
];
""",
        encoding="utf-8",
    )

    constellation = tmp_path / "frontend/src/constellation/constellationModel.ts"
    constellation.parent.mkdir(parents=True)
    constellation.write_text(
        """const VISUAL_METADATA = {
  // scaffold:visual-metadata:start
  // scaffold:visual-metadata:end
};
""",
        encoding="utf-8",
    )

    scaffold = ConnectorScaffold(tmp_path)
    plan = scaffold.plan(_manifest())

    written = scaffold.apply(plan)

    assert len(written) == 4
    assert all(path.exists() for path in written)
    assert "class DevdocsConnector:" in written[0].read_text(encoding="utf-8")
    assert "ping_devdocs" in written[1].read_text(encoding="utf-8")

    registry_content = registry.read_text(encoding="utf-8")
    assert 'id="devdocs"' in registry_content
    assert 'status_endpoint="/resources/devdocs/status"' in registry_content

    registry_test_content = registry_test.read_text(encoding="utf-8")
    assert '        "devdocs",' in registry_test_content

    api_content = api.read_text(encoding="utf-8")
    assert '@router.get("/devdocs/status")' in api_content
    assert "def devdocs_status()" in api_content

    frontend_content = frontend.read_text(encoding="utf-8")
    assert "id: 'devdocs'" in frontend_content
    assert "route: '/connectors?source=devdocs'" in frontend_content

    constellation_content = constellation.read_text(encoding="utf-8")
    assert "'devdocs': {" in constellation_content
    assert "healthEndpoint: '/resources/devdocs/status'" in constellation_content


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


def test_update_frontend_adds_connector(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend" / "src" / "models"
    frontend.mkdir(parents=True)

    frontend_file = frontend / "connectors.ts"
    frontend_file.write_text(
        """\
import {
  Layers3,
} from 'lucide-react'

const CONNECTORS = [
  // scaffold:connector-definitions:start
  // scaffold:connector-definitions:end
];
""",
        encoding="utf-8",
    )

    manifest = ConnectorManifest.from_mapping(
        {
            "id": "demo",
            "label": "Demo",
            "description": "Demo connector",
            "kind": "remote_api",
            "capabilities": ["demo.read"],
        }
    )

    changed = update_frontend(tmp_path, manifest)

    assert changed is True

    content = frontend_file.read_text(encoding="utf-8")

    assert "id: 'demo'" in content
    assert "label: 'Demo'" in content
    assert "// scaffold:connector-definitions:start" in content
    assert "// scaffold:connector-definitions:end" in content


def test_update_frontend_is_idempotent(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend" / "src" / "models"
    frontend.mkdir(parents=True)

    frontend_file = frontend / "connectors.ts"
    frontend_file.write_text(
        """\
import {
  Layers3,
} from 'lucide-react'

const CONNECTORS = [
  // scaffold:connector-definitions:start
  // scaffold:connector-definitions:end
];
""",
        encoding="utf-8",
    )

    manifest = ConnectorManifest.from_mapping(
        {
            "id": "demo",
            "label": "Demo",
            "description": "Demo connector",
            "kind": "remote_api",
            "capabilities": ["demo.read"],
        }
    )

    first_change = update_frontend(tmp_path, manifest)
    content_after_first_change = frontend_file.read_text(encoding="utf-8")

    second_change = update_frontend(tmp_path, manifest)
    content_after_second_change = frontend_file.read_text(encoding="utf-8")

    assert first_change is True
    assert second_change is False
    assert content_after_second_change == content_after_first_change
    assert content_after_second_change.count("id: 'demo'") == 1


def test_update_constellation_adds_visual_metadata(tmp_path: Path) -> None:
    constellation = tmp_path / "frontend" / "src" / "constellation"
    constellation.mkdir(parents=True)

    constellation_file = constellation / "constellationModel.ts"
    constellation_file.write_text(
        """\
const VISUAL_METADATA = {
  existing: {
    x: 10,
    y: 20,
  },

  // scaffold:visual-metadata:start
  // scaffold:visual-metadata:end
};
""",
        encoding="utf-8",
    )

    manifest = ConnectorManifest.from_mapping(
        {
            "id": "demo",
            "label": "Demo",
            "description": "Demo connector",
            "kind": "remote_api",
            "capabilities": ["demo.read"],
            "frontend": {
                "constellation": {
                    "x": 61,
                    "y": 37,
                    "size": "medium",
                    "palette": "azure",
                    "family": "crystalline",
                }
            },
        }
    )

    changed = update_constellation(tmp_path, manifest)

    assert changed is True

    content = constellation_file.read_text(encoding="utf-8")

    assert "existing:" in content
    assert "'demo': {" in content
    assert "x: 61" in content
    assert "y: 37" in content
    assert "size: 'medium'" in content
    assert "palette: 'azure'" in content
    assert "family: 'crystalline'" in content
    assert "healthEndpoint: '/resources/demo/status'" in content
    assert "// scaffold:visual-metadata:start" in content
    assert "// scaffold:visual-metadata:end" in content


def test_update_constellation_is_idempotent(tmp_path: Path) -> None:
    constellation = tmp_path / "frontend" / "src" / "constellation"
    constellation.mkdir(parents=True)

    constellation_file = constellation / "constellationModel.ts"
    constellation_file.write_text(
        """\
const VISUAL_METADATA = {
  // scaffold:visual-metadata:start
  // scaffold:visual-metadata:end
};
""",
        encoding="utf-8",
    )

    manifest = ConnectorManifest.from_mapping(
        {
            "id": "demo",
            "label": "Demo",
            "description": "Demo connector",
            "kind": "remote_api",
            "capabilities": ["demo.read"],
        }
    )

    first_change = update_constellation(tmp_path, manifest)
    content_after_first_change = constellation_file.read_text(encoding="utf-8")

    second_change = update_constellation(tmp_path, manifest)
    content_after_second_change = constellation_file.read_text(encoding="utf-8")

    assert first_change is True
    assert second_change is False
    assert content_after_second_change == content_after_first_change
    assert content_after_second_change.count("'demo': {") == 1


def test_apply_rolls_back_all_integrations_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    registry_test = tmp_path / "tests/services/test_connectors_registry.py"
    registry_test.parent.mkdir(parents=True)
    registry_test.write_text(
        """def test_registry_contains_existing_connectors() -> None:
    expected = {
        # scaffold:connector-ids:start
        # scaffold:connector-ids:end
    }
""",
        encoding="utf-8",
    )

    api = tmp_path / "src/hanuman/api/routers/resources.py"
    api.parent.mkdir(parents=True)
    api.write_text(
        '''router = APIRouter(prefix="/resources")

# scaffold:connector-routes:start

# scaffold:connector-routes:end
''',
        encoding="utf-8",
    )

    frontend = tmp_path / "frontend/src/models/connectors.ts"
    frontend.parent.mkdir(parents=True)
    frontend.write_text(
        """import {
  Layers3,
} from 'lucide-react'

const CONNECTORS = [
  // scaffold:connector-definitions:start
  // scaffold:connector-definitions:end
];
""",
        encoding="utf-8",
    )
    constellation = tmp_path / "frontend/src/constellation/constellationModel.ts"
    constellation.parent.mkdir(parents=True)
    constellation.write_text(
        """const VISUAL_METADATA = {
  // scaffold:visual-metadata:start
  // scaffold:visual-metadata:end
};
""",
        encoding="utf-8",
    )

    integration_files = (
        registry,
        registry_test,
        api,
        frontend,
        constellation,
    )
    contents_before = {path: path.read_bytes() for path in integration_files}

    def fail_constellation(
        project_root: Path,
        manifest: ConnectorManifest,
    ) -> bool:
        raise OSError("constellation failure")

    monkeypatch.setattr(
        "hanuman.scaffold.connector.update_constellation",
        fail_constellation,
    )

    scaffold = ConnectorScaffold(tmp_path)
    plan = scaffold.plan(_manifest())

    with pytest.raises(OSError, match="constellation failure"):
        scaffold.apply(plan)

    for path, content_before in contents_before.items():
        assert path.read_bytes() == content_before

    for planned_file in plan.files:
        assert not (tmp_path / planned_file.path).exists()


@pytest.mark.parametrize(
    ("kind", "expected"),
    (
        ("remote_api", "Adaptateur HTTP initial"),
        ("local_program", "Adaptateur initial du programme local"),
        ("local_filesystem", "Adaptateur initial du système de fichiers"),
        ("ai_provider", "Adaptateur initial du fournisseur IA"),
    ),
)
def test_plan_generates_connector_template_for_kind(
    tmp_path: Path,
    kind: str,
    expected: str,
) -> None:
    manifest = ConnectorManifest.from_mapping(
        {
            "id": "example",
            "label": "Example",
            "description": "Connecteur de test.",
            "kind": kind,
            "capabilities": ["example.read"],
        }
    )

    plan = ConnectorScaffold(tmp_path).plan(manifest)

    connector_file = plan.files[0]

    assert connector_file.path == Path("src/hanuman/services/connectors/example.py")
    assert expected in connector_file.content
    assert "class ExampleConnector:" in connector_file.content
    assert "def healthcheck(self) -> bool:" in connector_file.content


def test_update_frontend_imports_manifest_icon(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend/src/models/connectors.ts"
    frontend.parent.mkdir(parents=True)
    frontend.write_text(
        """import {
  BookOpen,
} from 'lucide-react'

const CONNECTORS = [
  // scaffold:connector-definitions:start
  // scaffold:connector-definitions:end
]
""",
        encoding="utf-8",
    )

    manifest = ConnectorManifest.from_mapping(
        {
            "id": "contacts",
            "label": "Google Contacts",
            "description": "Consultation des contacts Google.",
            "kind": "remote_api",
            "capabilities": ["contacts.read"],
            "frontend": {
                "icon": "ContactRound",
            },
        }
    )

    assert update_frontend(tmp_path, manifest) is True

    rendered = frontend.read_text(encoding="utf-8")
    assert "  ContactRound,\n} from 'lucide-react'" in rendered
    assert "icon: ContactRound" in rendered


def test_update_frontend_does_not_duplicate_manifest_icon(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend/src/models/connectors.ts"
    frontend.parent.mkdir(parents=True)
    frontend.write_text(
        """import {
  ContactRound,
} from 'lucide-react'

const CONNECTORS = [
  // scaffold:connector-definitions:start
  // scaffold:connector-definitions:end
]
""",
        encoding="utf-8",
    )

    manifest = ConnectorManifest.from_mapping(
        {
            "id": "contacts",
            "label": "Google Contacts",
            "description": "Consultation des contacts Google.",
            "kind": "remote_api",
            "capabilities": ["contacts.read"],
            "frontend": {
                "icon": "ContactRound",
            },
        }
    )

    assert update_frontend(tmp_path, manifest) is True
    assert update_frontend(tmp_path, manifest) is False

    rendered = frontend.read_text(encoding="utf-8")
    assert rendered.count("icon: ContactRound") == 1
    assert rendered.count("id: 'contacts'") == 1
    assert rendered.count("import {\n  ContactRound,") == 1


def test_update_frontend_sorts_lucide_icon_imports(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend/src/models/connectors.ts"
    frontend.parent.mkdir(parents=True)
    frontend.write_text(
        """import {
  Network,
  BookOpen,
} from 'lucide-react'

const CONNECTORS = [
  // scaffold:connector-definitions:start
  // scaffold:connector-definitions:end
]
""",
        encoding="utf-8",
    )

    manifest = ConnectorManifest.from_mapping(
        {
            "id": "contacts",
            "label": "Google Contacts",
            "description": "Consultation des contacts Google.",
            "kind": "remote_api",
            "capabilities": ["contacts.read"],
            "frontend": {
                "icon": "ContactRound",
            },
        }
    )

    assert update_frontend(tmp_path, manifest) is True

    rendered = frontend.read_text(encoding="utf-8")

    assert (
        """import {
  BookOpen,
  ContactRound,
  Network,
} from 'lucide-react'
"""
        in rendered
    )
