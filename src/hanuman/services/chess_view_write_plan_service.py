from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hanuman.services.atomic_write_service import atomic_write_text
from hanuman.services.chess_generated_frontmatter_service import (
    update_generated_frontmatter,
)
from hanuman.services.chess_path_safety_service import resolve_safe_destination
from hanuman.services.delimited_zone_service import replace_delimited_zone


class ChessViewValidationError(ValueError):
    """Signale une vue impossible à valider avant la phase d’écriture."""


@dataclass(frozen=True)
class ChessPlannedWrite:
    path: Path
    content: str


@dataclass(frozen=True)
class ChessProtectedFile:
    path: Path
    reason: str


@dataclass(frozen=True)
class ChessViewWritePlan:
    writes: tuple[ChessPlannedWrite, ...] = ()
    protected_files: tuple[ChessProtectedFile, ...] = ()

    def merged(self, other: ChessViewWritePlan) -> ChessViewWritePlan:
        writes = self.writes + other.writes
        paths = [item.path for item in writes]
        if len(paths) != len(set(paths)):
            raise ChessViewValidationError(
                "Une destination de vue Chess est planifiée plusieurs fois."
            )
        return ChessViewWritePlan(
            writes=writes,
            protected_files=self.protected_files + other.protected_files,
        )

    def execute(self) -> None:
        for item in sorted(self.writes, key=lambda planned: str(planned.path)):
            atomic_write_text(item.path, item.content)


def plan_generated_view(
    root: Path,
    path: Path,
    *,
    initial: str,
    generated: str,
    start_marker: str,
    end_marker: str,
    owned_frontmatter_keys: frozenset[str] = frozenset(),
) -> ChessViewWritePlan:
    safe_path = resolve_safe_destination(root, path)
    if not safe_path.exists():
        return ChessViewWritePlan(writes=(ChessPlannedWrite(safe_path, initial),))
    if not safe_path.is_file():
        raise ChessViewValidationError(f"Destination Chess non régulière : {safe_path}")
    try:
        existing = safe_path.read_text(encoding="utf-8")
        existing_with_generated_zone = replace_delimited_zone(
            existing,
            generated,
            start_marker,
            end_marker,
            label="de vue Hanuman",
        )
        if existing_with_generated_zone is None:
            return ChessViewWritePlan(
                protected_files=(
                    ChessProtectedFile(
                        safe_path,
                        "Fichier humain sans marqueurs Hanuman, laissé intact.",
                    ),
                )
            )
        updated_frontmatter = (
            update_generated_frontmatter(
                existing_with_generated_zone,
                initial,
                owned_keys=owned_frontmatter_keys,
                label="de vue Hanuman",
            )
            if owned_frontmatter_keys
            else existing_with_generated_zone
        )
        updated = updated_frontmatter
    except (OSError, UnicodeError, ValueError) as exc:
        raise ChessViewValidationError(f"Vue Chess invalide {safe_path} : {exc}") from exc
    return ChessViewWritePlan(writes=(ChessPlannedWrite(safe_path, updated),))
