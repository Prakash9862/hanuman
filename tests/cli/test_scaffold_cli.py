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
