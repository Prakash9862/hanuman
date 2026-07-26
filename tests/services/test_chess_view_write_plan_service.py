from pathlib import Path

import pytest

from hanuman.services.chess_view_write_plan_service import (
    ChessViewValidationError,
    plan_generated_view,
)

START = "<!-- START -->"
END = "<!-- END -->"


def test_plan_does_not_write_before_execution(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    path = root / "_Index/Test.md"

    plan = plan_generated_view(
        root,
        path,
        initial=f"{START}\nnew\n{END}",
        generated=f"{START}\nnew\n{END}",
        start_marker=START,
        end_marker=END,
    )

    assert not path.exists()
    plan.execute()
    assert path.read_text(encoding="utf-8") == f"{START}\nnew\n{END}"


def test_invalid_late_view_leaves_earlier_plan_unwritten(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    first = root / "_Index/First.md"
    last = root / "_Index/Last.md"
    first.parent.mkdir(parents=True)
    first.write_text(f"{START}\nold\n{END}", encoding="utf-8")
    last.write_text(f"{START}\ninvalid", encoding="utf-8")
    before = first.read_bytes()

    plan_generated_view(
        root,
        first,
        initial="unused",
        generated=f"{START}\nnew\n{END}",
        start_marker=START,
        end_marker=END,
    )
    with pytest.raises(ChessViewValidationError):
        plan_generated_view(
            root,
            last,
            initial="unused",
            generated=f"{START}\nnew\n{END}",
            start_marker=START,
            end_marker=END,
        )

    assert first.read_bytes() == before
