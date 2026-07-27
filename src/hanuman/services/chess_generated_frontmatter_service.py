from __future__ import annotations

import json
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
_BLOCK_TAG = re.compile(r"^[ \t]+-[ \t]+(.+?)(?:\r?\n)?$")
_FLOW_TAGS = re.compile(r"^(tags:[ \t]*)\[(.*)\]([ \t]*)(?:\r?\n)?$")
CHESS_MANAGED_TAG_PREFIXES = ("chess/",)


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
    managed_tag_prefixes: tuple[str, ...] = (),
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
            if key == "tags" and managed_tag_prefixes:
                replacements[current_start] = (
                    current_end,
                    _merge_tags(
                        current.lines[current_start:current_end],
                        desired.lines[desired_start:desired_end],
                        managed_prefixes=managed_tag_prefixes,
                        newline=current.newline,
                        label=label,
                    ),
                )
                continue
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


def _decode_tag(raw: str, *, label: str) -> str:
    value = raw.strip()
    if not value:
        raise ChessGeneratedFrontmatterError(f"Tag vide ou ambigu dans {label}.")
    if value.startswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ChessGeneratedFrontmatterError(
                f"Tag entre guillemets doubles invalide dans {label}."
            ) from exc
        if not isinstance(decoded, str):
            raise ChessGeneratedFrontmatterError(f"Tag non textuel dans {label}.")
        return decoded
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise ChessGeneratedFrontmatterError(
                f"Tag entre guillemets simples invalide dans {label}."
            )
        return value[1:-1].replace("''", "'")
    if any(character in value for character in "#,[]{}") or any(
        character.isspace() for character in value
    ):
        raise ChessGeneratedFrontmatterError(
            f"Format de tag non pris en charge dans {label} : {value!r}."
        )
    return value


def _split_flow_tags(content: str, *, label: str) -> list[str]:
    values: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    for index, character in enumerate(content):
        if quote == '"' and character == "\\" and not escaped:
            escaped = True
            continue
        if character in {"'", '"'} and not escaped:
            if quote is None:
                quote = character
            elif quote == character:
                quote = None
        elif character == "," and quote is None:
            values.append(content[start:index].strip())
            start = index + 1
        escaped = False
    if quote is not None:
        raise ChessGeneratedFrontmatterError(f"Liste de tags non fermée dans {label}.")
    tail = content[start:].strip()
    if tail:
        values.append(tail)
    elif content.strip():
        raise ChessGeneratedFrontmatterError(f"Tag vide dans {label}.")
    return values


def _tag_entries(lines: tuple[str, ...], *, label: str) -> tuple[str, list[tuple[str, str]]]:
    header = lines[0].rstrip("\r\n")
    flow = _FLOW_TAGS.fullmatch(lines[0])
    if flow is not None:
        raw_values = _split_flow_tags(flow.group(2), label=label)
        return "flow", [(raw, _decode_tag(raw, label=label)) for raw in raw_values]
    if header.strip() != "tags:":
        raise ChessGeneratedFrontmatterError(f"Format de tags non pris en charge dans {label}.")
    entries: list[tuple[str, str]] = []
    for line in lines[1:]:
        match = _BLOCK_TAG.fullmatch(line)
        if match is None:
            raise ChessGeneratedFrontmatterError(f"Liste de tags multiligne ambiguë dans {label}.")
        raw = match.group(1)
        entries.append((raw, _decode_tag(raw, label=label)))
    return "block", entries


def _merge_tags(
    existing_lines: tuple[str, ...],
    desired_lines: tuple[str, ...],
    *,
    managed_prefixes: tuple[str, ...],
    newline: str,
    label: str,
) -> tuple[str, ...]:
    style, existing = _tag_entries(existing_lines, label=label)
    _, desired = _tag_entries(desired_lines, label=f"{label} généré")
    human: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw, value in existing:
        if value.startswith(managed_prefixes) or value in seen:
            continue
        human.append((raw, value))
        seen.add(value)
    managed: list[tuple[str, str]] = []
    for raw, value in desired:
        if not value.startswith(managed_prefixes):
            raise ChessGeneratedFrontmatterError(f"Tag non géré {value!r} dans le modèle {label}.")
        if value not in seen:
            managed.append((raw, value))
            seen.add(value)
    merged = human + managed
    if style == "flow":
        return (f"tags: [{', '.join(raw for raw, _ in merged)}]{newline}",)
    return (
        f"tags:{newline}",
        *(f"  - {raw}{newline}" for raw, _ in merged),
    )
