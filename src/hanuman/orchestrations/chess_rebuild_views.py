from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from hanuman.services.chess_view_rebuild_service import rebuild_chess_views


class UnsafeChessVaultPathError(ValueError):
    """Signale une cible impropre à une reconstruction de vues."""


def validate_chess_vault_path(raw_path: str) -> Path:
    if not raw_path.strip():
        raise UnsafeChessVaultPathError("Le chemin de vault ne peut pas être vide.")
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise UnsafeChessVaultPathError(f"Le chemin n’existe pas : {path}")
    if not path.is_dir():
        raise UnsafeChessVaultPathError(f"Le chemin n’est pas un dossier : {path}")
    if path == Path("/"):
        raise UnsafeChessVaultPathError("La racine système / est interdite.")
    if path == Path.home().resolve():
        raise UnsafeChessVaultPathError("Le dossier personnel seul est interdit.")
    repository_root = Path(__file__).resolve().parents[3]
    if path == repository_root or repository_root in path.parents:
        raise UnsafeChessVaultPathError("Un chemin situé dans le dépôt source est interdit.")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hanuman chess rebuild-views",
        description="Reconstruit uniquement les vues Chess dérivées, sans réseau ni Stockfish.",
    )
    parser.add_argument(
        "--vault-path",
        required=True,
        help="Chemin explicite de la racine Chess à reconstruire.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = validate_chess_vault_path(args.vault_path)
        report = rebuild_chess_views(root)
    except (UnsafeChessVaultPathError, OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"Erreur de reconstruction Chess : {exc}\n")
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
