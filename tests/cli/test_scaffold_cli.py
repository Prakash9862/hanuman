from __future__ import annotations

import hanuman.cli as cli


def test_parser_accepts_connector_scaffold_dry_run() -> None:
    args = cli._parser().parse_args(
        [
            "scaffold",
            "connector",
            "connectors/devdocs.yml",
            "--dry-run",
        ]
    )

    assert args.command == "scaffold"
    assert args.scaffold_resource == "connector"
    assert args.manifest == "connectors/devdocs.yml"
    assert args.dry_run is True
    assert args.force is False


def test_parser_accepts_connector_scaffold_force() -> None:
    args = cli._parser().parse_args(
        [
            "scaffold",
            "connector",
            "connectors/devdocs.yml",
            "--force",
        ]
    )

    assert args.command == "scaffold"
    assert args.scaffold_resource == "connector"
    assert args.manifest == "connectors/devdocs.yml"
    assert args.dry_run is False
    assert args.force is True


def test_connector_scaffold_dry_run_prints_plan_without_writing(
    tmp_path,
    monkeypatch,
) -> None:
    from io import StringIO

    from rich.console import Console

    manifest = tmp_path / "connectors" / "devdocs.yml"
    manifest.parent.mkdir()
    manifest.write_text(
        """
id: devdocs
label: DevDocs
description: Documentation technique.
kind: remote_api
capabilities:
  - documentation.search
workspace: search
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    output = StringIO()
    exit_code = cli.run_cli(
        [
            "scaffold",
            "connector",
            "connectors/devdocs.yml",
            "--dry-run",
        ],
        console=Console(file=output, force_terminal=False, width=120),
    )

    assert exit_code == 0
    rendered = output.getvalue()
    assert "Dry-run" in rendered
    assert "src/hanuman/services/core/devdocs_service.py" in rendered
    assert "tests/services/test_devdocs_service.py" in rendered
    assert "docs/connectors/devdocs.md" in rendered
    assert not (tmp_path / "src/hanuman/services/core/devdocs_service.py").exists()


def _write_manifest(tmp_path) -> None:
    manifest = tmp_path / "connectors" / "example.yml"
    manifest.parent.mkdir(exist_ok=True)
    manifest.write_text(
        """
id: example
label: Example
description: Connecteur utilisé pour tester le scaffold.
kind: remote_api
capabilities:
  - example.read
workspace: catalog-only
""".strip(),
        encoding="utf-8",
    )

    registry = tmp_path / "src/hanuman/services/connectors_registry.py"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        """_CONNECTORS = (
    # scaffold:connectors:start

    # scaffold:connectors:end
)
""",
        encoding="utf-8",
    )


def test_connector_scaffold_write_mode_creates_planned_files(
    tmp_path,
    monkeypatch,
) -> None:
    from io import StringIO

    from rich.console import Console

    _write_manifest(tmp_path)
    monkeypatch.chdir(tmp_path)

    output = StringIO()
    exit_code = cli.run_cli(
        [
            "scaffold",
            "connector",
            "connectors/example.yml",
        ],
        console=Console(file=output, force_terminal=False, width=120),
    )

    assert exit_code == 0
    assert (tmp_path / "src/hanuman/services/core/example_service.py").is_file()
    assert (tmp_path / "tests/services/test_example_service.py").is_file()
    assert (tmp_path / "docs/connectors/example.md").is_file()

    rendered = output.getvalue()
    assert "Connecteur Example généré" in rendered
    assert "src/hanuman/services/core/example_service.py" in rendered


def test_connector_scaffold_refuses_existing_files(
    tmp_path,
    monkeypatch,
) -> None:
    from io import StringIO

    from rich.console import Console

    _write_manifest(tmp_path)
    existing = tmp_path / "src/hanuman/services/core/example_service.py"
    existing.parent.mkdir(parents=True)
    existing.write_text("# fichier existant\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    output = StringIO()
    exit_code = cli.run_cli(
        [
            "scaffold",
            "connector",
            "connectors/example.yml",
        ],
        console=Console(file=output, force_terminal=False, width=120),
    )

    assert exit_code == 2
    assert "refuse d'écraser" in output.getvalue()
    assert existing.read_text(encoding="utf-8") == "# fichier existant\n"


def test_connector_scaffold_force_replaces_existing_files(
    tmp_path,
    monkeypatch,
) -> None:
    from io import StringIO

    from rich.console import Console

    _write_manifest(tmp_path)
    existing = tmp_path / "src/hanuman/services/core/example_service.py"
    existing.parent.mkdir(parents=True)
    existing.write_text("# fichier existant\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    output = StringIO()
    exit_code = cli.run_cli(
        [
            "scaffold",
            "connector",
            "connectors/example.yml",
            "--force",
        ],
        console=Console(file=output, force_terminal=False, width=120),
    )

    assert exit_code == 0
    assert existing.read_text(encoding="utf-8") != "# fichier existant\n"
    assert "class ExampleStatus" in existing.read_text(encoding="utf-8")
