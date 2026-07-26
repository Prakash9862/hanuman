from __future__ import annotations

import re
from dataclasses import dataclass


class ChessGeneratedFrontmatterError(ValueError):
    """Signale un frontmatter impossible à actualiser sans perte."""


@dataclass(frozen=True)
class _Frontmatter:
    lines: tuple[str, ...]
    closing_index: int
    spans: dict[str, tuple[int, int]]
    newline: str


_KEY_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t].*)?(?:\r?\n)?$")


def _parse_frontmatter(markdown: str, *, label: str) -> _Frontmatter:
    lines = tuple(markdown.splitlines(keepends=True))
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ChessGeneratedFrontmatterError(f"Frontmatter {label} absent ou invalide.")

    closing = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.rstrip("\r\n") == "---"),
        None,
    )
    if closing is None:
        raise ChessGeneratedFrontmatterError(f"Frontmatter {label} non fermé.")

    starts: list[tuple[str, int]] = []
    seen: set[str] = set()
    for index in range(1, closing):
        line = lines[index]
        if line.startswith((" ", "\t")) or not line.strip() or line.lstrip().startswith("#"):
            continue
        match = _KEY_LINE.fullmatch(line)
        if match is None:
            raise ChessGeneratedFrontmatterError(
                f"Frontmatter {label} ambigu à la ligne {index + 1}."
            )
        key = match.group(1)
        if key in seen:
            raise ChessGeneratedFrontmatterError(
                f"Clé de frontmatter {key!r} dupliquée dans {label}."
            )
        seen.add(key)
        starts.append((key, index))

    spans = {
        key: (start, starts[position + 1][1] if position + 1 < len(starts) else closing)
        for position, (key, start) in enumerate(starts)
    }
    newline = "\r\n" if lines[0].endswith("\r\n") else "\n"
    return _Frontmatter(lines, closing, spans, newline)


def update_generated_frontmatter(
    existing: str,
    generated: str,
    *,
    owned_keys: frozenset[str],
    label: str,
) -> str:
    """Actualise les seules clés Hanuman en conservant le reste octet pour octet."""

    current = _parse_frontmatter(existing, label=label)
    desired = _parse_frontmatter(generated, label=f"{label} généré")
    missing_desired = owned_keys - desired.spans.keys()
    if missing_desired:
        missing = ", ".join(sorted(missing_desired))
        raise ChessGeneratedFrontmatterError(
            f"Clés Hanuman absentes du modèle {label} : {missing}."
        )

    replacements: dict[int, tuple[int, tuple[str, ...]]] = {}
    additions: list[str] = []
    for key in owned_keys:
        desired_start, desired_end = desired.spans[key]
        desired_lines = tuple(
            line.rstrip("\r\n") + current.newline
            for line in desired.lines[desired_start:desired_end]
        )
        if key in current.spans:
            current_start, current_end = current.spans[key]
            source_line = current.lines[current_start].rstrip("\r\n")
            owned_span = current.lines[current_start:current_end]
            if re.search(r"\s+#", source_line) or any(
                line.lstrip().startswith("#") for line in owned_span[1:]
            ):
                raise ChessGeneratedFrontmatterError(
                    f"Commentaire sur la clé Hanuman {key!r} dans {label}."
                )
            replacements[current_start] = (current_end, desired_lines)
        else:
            additions.extend(desired_lines)

    output: list[str] = []
    index = 0
    while index < len(current.lines):
        replacement = replacements.get(index)
        if replacement is not None:
            end, lines = replacement
            output.extend(lines)
            index = end
            continue
        if index == current.closing_index:
            output.extend(additions)
        output.append(current.lines[index])
        index += 1
    return "".join(output)
