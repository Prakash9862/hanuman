from __future__ import annotations

import pytest

from hanuman.scaffold.markers import MarkerError, replace_between_markers

START = "# scaffold:connectors:start"
END = "# scaffold:connectors:end"


def test_replace_between_markers_inserts_generated_content() -> None:
    source = f"""before
{START}
old content
{END}
after
"""

    result = replace_between_markers(
        source,
        start_marker=START,
        end_marker=END,
        content="generated content",
    )

    assert (
        result
        == f"""before
{START}
generated content
{END}
after
"""
    )


def test_replace_between_markers_is_idempotent() -> None:
    source = f"""before
{START}
{END}
after
"""

    first = replace_between_markers(
        source,
        start_marker=START,
        end_marker=END,
        content="generated content",
    )
    second = replace_between_markers(
        first,
        start_marker=START,
        end_marker=END,
        content="generated content",
    )

    assert second == first


def test_replace_between_markers_accepts_empty_content() -> None:
    source = f"""before
{START}
old content
{END}
after
"""

    result = replace_between_markers(
        source,
        start_marker=START,
        end_marker=END,
        content="",
    )

    assert (
        result
        == f"""before
{START}
{END}
after
"""
    )


def test_replace_between_markers_rejects_missing_marker() -> None:
    with pytest.raises(MarkerError, match="Marqueur absent"):
        replace_between_markers(
            f"{START}\n",
            start_marker=START,
            end_marker=END,
            content="generated",
        )


def test_replace_between_markers_rejects_duplicate_marker() -> None:
    source = f"""{START}
{START}
{END}
"""

    with pytest.raises(MarkerError, match="Marqueur dupliqué"):
        replace_between_markers(
            source,
            start_marker=START,
            end_marker=END,
            content="generated",
        )


def test_replace_between_markers_rejects_reversed_markers() -> None:
    source = f"""{END}
{START}
"""

    with pytest.raises(MarkerError, match="doit précéder"):
        replace_between_markers(
            source,
            start_marker=START,
            end_marker=END,
            content="generated",
        )
