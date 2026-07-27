from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

from hanuman.config.env import chess_player_name
from hanuman.orchestrations.chess_analysis import (
    _game_paths,
    _validated_chess_root,
    analyse_note,
)
from hanuman.services.chess_analysis_service import AnalysisConfig, StockfishAnalyzer
from hanuman.services.chess_insight_storage_service import parse_insight_block


def _is_v2(path: Path) -> bool:
    try:
        envelope = parse_insight_block(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return False
    return envelope is not None and envelope.schema_version >= 2


def upgrade_analyses(
    *,
    root: Path | None = None,
    limit: int | None = None,
    path_filter: str | None = None,
    depth: int = 18,
    force: bool = False,
) -> dict[str, object]:
    """Réanalyse volontairement un lot; une note V1 reste intacte en cas d'échec."""

    selected_root = root or _validated_chess_root()
    paths = _game_paths(selected_root)
    if path_filter:
        paths = [path for path in paths if path_filter in str(path.relative_to(selected_root))]

    already_current = [path for path in paths if _is_v2(path) and not force]
    pending = [path for path in paths if force or not _is_v2(path)]
    if limit is not None:
        pending = pending[:limit]

    analysed = 0
    skipped = max(0, len(paths) - len(already_current) - len(pending))
    failed: list[dict[str, str]] = []
    config = AnalysisConfig(
        engine_path=os.environ.get("STOCKFISH_PATH"),
        depth=depth,
        player_name=chess_player_name(),
    )
    if pending:
        with StockfishAnalyzer(config) as analyzer:
            for index, path in enumerate(pending, start=1):
                relative = str(path.relative_to(selected_root))
                print(f"[{index}/{len(pending)}] {relative}", flush=True)
                try:
                    result = analyse_note(path, analyzer, root=selected_root)
                    if result is None:
                        skipped += 1
                    else:
                        analysed += 1
                except Exception as exc:  # noqa: BLE001 - bilan par note et reprise possible
                    failed.append({"path": relative, "error": str(exc)})

    return {
        "status": "ok" if not failed else "partial",
        "root": str(selected_root),
        "analysed": analysed,
        "skipped": skipped,
        "failed": failed,
        "already_current": len(already_current),
        "selected": len(pending),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hanuman chess upgrade-analyses",
        description="Met à niveau explicitement des analyses Chess V1 vers Stockfish V2.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--filter", dest="path_filter")
    parser.add_argument("--depth", type=int, default=18)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = upgrade_analyses(
        limit=args.limit,
        path_filter=args.path_filter,
        depth=args.depth,
        force=args.force,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
