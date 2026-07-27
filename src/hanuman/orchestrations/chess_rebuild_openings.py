from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Sequence

from hanuman.orchestrations.chess_rebuild_views import validate_chess_vault_path
from hanuman.services.chess_eco_page_service import (
    resolve_eco_reference_pdf,
    write_eco_pages,
)
from hanuman.services.chess_vault_reader_service import read_chess_vault


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hanuman chess rebuild-openings",
        description="Reconstruit uniquement les pages ECO générées depuis le vault.",
    )
    parser.add_argument("--vault-path", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = validate_chess_vault_path(args.vault_path)
        read_result = read_chess_vault(root)
        if read_result.ignored_notes:
            raise ValueError(f"{len(read_result.ignored_notes)} note(s) chess-game illisible(s).")
        report = write_eco_pages(
            root,
            list(read_result.games),
            theory_pdf=resolve_eco_reference_pdf(),
        )
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"Erreur de reconstruction ECO : {exc}") from exc
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
