from __future__ import annotations

from dataclasses import dataclass


class DelimitedZoneError(ValueError):
    """Signale une zone générée dont les marqueurs sont ambigus."""


@dataclass(frozen=True)
class DelimitedZone:
    start: int
    end: int


def find_delimited_zone(
    content: str,
    start_marker: str,
    end_marker: str,
    *,
    label: str,
) -> DelimitedZone | None:
    starts = content.count(start_marker)
    ends = content.count(end_marker)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise DelimitedZoneError(f"Marqueurs {label} incomplets ou dupliqués.")
    start = content.index(start_marker)
    end_start = content.index(end_marker)
    if end_start < start:
        raise DelimitedZoneError(f"Marqueurs {label} dans un ordre invalide.")
    return DelimitedZone(start=start, end=end_start + len(end_marker))


def extract_delimited_zone(
    content: str,
    start_marker: str,
    end_marker: str,
    *,
    label: str,
) -> str | None:
    bounds = find_delimited_zone(content, start_marker, end_marker, label=label)
    if bounds is None:
        return None
    return content[bounds.start : bounds.end]


def replace_delimited_zone(
    content: str,
    replacement: str,
    start_marker: str,
    end_marker: str,
    *,
    label: str,
) -> str | None:
    bounds = find_delimited_zone(content, start_marker, end_marker, label=label)
    if bounds is None:
        return None
    return content[: bounds.start] + replacement + content[bounds.end :]
