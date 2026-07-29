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


def test_connector_scaffold_refuses_write_mode_for_now(tmp_path) -> None:
    from io import StringIO

    from rich.console import Console

    output = StringIO()
    exit_code = cli.run_cli(
        [
            "scaffold",
            "connector",
            str(tmp_path / "devdocs.yml"),
        ],
        console=Console(file=output, force_terminal=False, width=120),
    )

    assert exit_code == 2
    assert "pas encore activée" in output.getvalue()
