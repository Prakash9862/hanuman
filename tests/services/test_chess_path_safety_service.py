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


def test_refuses_symbolic_root(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    symbolic_root = tmp_path / "symbolic"
    real_root.mkdir()
    symbolic_root.symlink_to(real_root, target_is_directory=True)

    with pytest.raises(UnsafeChessDestinationError, match="Racine Chess symbolique"):
        resolve_safe_destination(symbolic_root, symbolic_root / "Dashboard.md")


def test_accepts_nonexistent_real_root(tmp_path: Path) -> None:
    root = tmp_path / "new-root"

    assert resolve_safe_destination(root, root / "safe.md") == root / "safe.md"


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


def test_refuses_broken_final_symlink(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    target = root / "Dashboard.md"
    root.mkdir()
    target.symlink_to(tmp_path / "missing.md")

    with pytest.raises(UnsafeChessDestinationError, match="symbolique"):
        resolve_safe_destination(root, target)
