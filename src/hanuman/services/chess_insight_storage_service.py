from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from hanuman.models.chess_insight import ChessInsightEnvelope
from hanuman.services.delimited_zone_service import (
    DelimitedZoneError,
    find_delimited_zone,
)

INSIGHTS_START = "<!-- HANUMAN_CHESS_INSIGHTS_START -->"
INSIGHTS_END = "<!-- HANUMAN_CHESS_INSIGHTS_END -->"


class ChessInsightBlockError(ValueError):
    """Signale une zone technique d'insights absente ou mal délimitée."""


@dataclass(frozen=True)
class ChessNoteInsightMetadata:
    game_id: str | None
    eco: str | None
    player_color: Literal["white", "black"] | None


def render_insight_block(envelope: ChessInsightEnvelope) -> str:
    return f"{INSIGHTS_START}\n" "```json\n" f"{envelope.to_json()}\n" "```\n" f"{INSIGHTS_END}"


def _block_bounds(markdown: str) -> tuple[int, int] | None:
    try:
        bounds = find_delimited_zone(
            markdown,
            INSIGHTS_START,
            INSIGHTS_END,
            label="ChessInsight",
        )
    except DelimitedZoneError as exc:
        raise ChessInsightBlockError(str(exc)) from exc
    if bounds is None:
        return None
    return bounds.start, bounds.end


def inject_insight_block(markdown: str, envelope: ChessInsightEnvelope) -> str:
    rendered = render_insight_block(envelope)
    bounds = _block_bounds(markdown)
    if bounds is None:
        return markdown.rstrip() + "\n\n" + rendered + "\n"
    parse_insight_block(markdown)
    start, end = bounds
    return markdown[:start] + rendered + markdown[end:]


def parse_insight_block(markdown: str) -> ChessInsightEnvelope | None:
    bounds = _block_bounds(markdown)
    if bounds is None:
        return None
    start, end = bounds
    raw_block = markdown[start + len(INSIGHTS_START) : end - len(INSIGHTS_END)]
    content = raw_block.strip()
    if not content.startswith("```json") or not content.endswith("```"):
        raise ChessInsightBlockError("La zone ChessInsight doit contenir un bloc JSON clôturé.")
    raw_json = content[len("```json") : -len("```")].strip()
    return ChessInsightEnvelope.from_json(raw_json)


def extract_insight_block(markdown: str) -> str | None:
    bounds = _block_bounds(markdown)
    if bounds is None:
        return None
    parse_insight_block(markdown)
    start, end = bounds
    return markdown[start:end]


def read_note_insights(path: Path) -> ChessInsightEnvelope | None:
    return parse_insight_block(path.read_text(encoding="utf-8"))


def _frontmatter_scalar(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ChessInsightBlockError("Valeur de frontmatter JSON invalide.") from exc
        if not isinstance(decoded, str):
            raise ChessInsightBlockError("Valeur de frontmatter attendue sous forme de chaîne.")
        return decoded
    return value


def parse_chess_note_insight_metadata(markdown: str) -> ChessNoteInsightMetadata:
    if not markdown.startswith("---\n"):
        return ChessNoteInsightMetadata(None, None, None)
    end = markdown.find("\n---", 4)
    if end < 0:
        raise ChessInsightBlockError("Frontmatter Chess incomplet.")

    values: dict[str, str] = {}
    for line in markdown[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key in {"game_id", "eco", "color"}:
            values[key] = _frontmatter_scalar(value)

    color = values.get("color")
    if color is not None and color not in {"white", "black"}:
        raise ChessInsightBlockError("Couleur joueur invalide dans le frontmatter.")
    return ChessNoteInsightMetadata(
        game_id=values.get("game_id"),
        eco=values.get("eco"),
        player_color=cast(Literal["white", "black"] | None, color),
    )
