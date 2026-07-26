from pathlib import Path

import pytest

from hanuman.services.chess_path_safety_service import (
    UnsafeChessDestinationError,
    resolve_safe_destination,
)


def test_accepts_safe_new_unicode_destination(tmp_path: Path) -> None:
    root = tmp_path / "Échecs"
    root.mkdir()

    result = resolve_safe_destination(root, root / "_Index/Ouvertures/Échec.md")

    assert result == root / "_Index/Ouvertures/Échec.md"


@pytest.mark.parametrize("relative", ["_Index", "_Index/Ouvertures"])
def test_refuses_symlinked_parent_outside_root(tmp_path: Path, relative: str) -> None:
    root = tmp_path / "Echecs"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(outside, target_is_directory=True)

    with pytest.raises(UnsafeChessDestinationError, match="symbolique"):
        resolve_safe_destination(root, target / "Dashboard.md")


def test_refuses_final_file_symlink(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    outside = tmp_path / "outside.md"
    target = root / "_Index/Dashboard.md"
    target.parent.mkdir(parents=True)
    outside.write_text("outside", encoding="utf-8")
    target.symlink_to(outside)

    with pytest.raises(UnsafeChessDestinationError, match="symbolique"):
        resolve_safe_destination(root, target)


def test_refuses_parent_traversal(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    root.mkdir()

    with pytest.raises(UnsafeChessDestinationError, match="hors"):
        resolve_safe_destination(root, root / "../outside.md")
