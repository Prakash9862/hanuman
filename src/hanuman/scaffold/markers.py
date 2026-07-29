from __future__ import annotations


class MarkerError(ValueError):
    """Signale un point d'extension absent, dupliqué ou incohérent."""


def replace_between_markers(
    text: str,
    *,
    start_marker: str,
    end_marker: str,
    content: str,
) -> str:
    """Remplace uniquement le contenu situé entre deux marqueurs uniques."""

    _validate_marker(text, start_marker)
    _validate_marker(text, end_marker)

    start_index = text.index(start_marker)
    end_index = text.index(end_marker)

    if start_index >= end_index:
        raise MarkerError(
            f"Le marqueur de début {start_marker!r} doit précéder "
            f"le marqueur de fin {end_marker!r}."
        )

    start_line_end = text.find("\n", start_index)
    if start_line_end == -1:
        raise MarkerError(f"Le marqueur de début {start_marker!r} doit occuper une ligne complète.")

    end_line_start = text.rfind("\n", 0, end_index)
    if end_line_start == -1:
        end_line_start = 0
    else:
        end_line_start += 1

    generated = content.rstrip("\n")

    replacement = "\n"
    if generated:
        replacement += generated + "\n"

    return text[:start_line_end] + replacement + text[end_line_start:]


def _validate_marker(text: str, marker: str) -> None:
    count = text.count(marker)

    if count == 0:
        raise MarkerError(f"Marqueur absent : {marker!r}.")

    if count > 1:
        raise MarkerError(f"Marqueur dupliqué : {marker!r}.")
