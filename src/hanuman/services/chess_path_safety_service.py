from __future__ import annotations

import os
from pathlib import Path


class UnsafeChessDestinationError(ValueError):
    """Signale une destination Chess qui sort de sa racine ou traverse un symlink."""


def resolve_safe_destination(root: Path, destination: Path) -> Path:
    expanded_root = root.expanduser()
    if expanded_root.is_symlink():
        raise UnsafeChessDestinationError(f"Racine Chess symbolique interdite : {expanded_root}")
    resolved_root = expanded_root.resolve()
    candidate = destination if destination.is_absolute() else resolved_root / destination
    lexical_candidate = Path(os.path.abspath(candidate))
    try:
        relative = lexical_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise UnsafeChessDestinationError(
            f"Destination Chess hors de la racine autorisée : {destination}"
        ) from exc

    current = resolved_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise UnsafeChessDestinationError(
                f"Chemin symbolique interdit pour une écriture Chess : {current}"
            )
        if not current.exists():
            break

    resolved_candidate = lexical_candidate.resolve(strict=False)
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise UnsafeChessDestinationError(
            f"Destination Chess résolue hors de la racine : {destination}"
        ) from exc
    return lexical_candidate
