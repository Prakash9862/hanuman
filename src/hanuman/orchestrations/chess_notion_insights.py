from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from hanuman.services.core.notion_service import NotionPageRef, NotionService


def _heading(text: str, level: int = 2) -> Dict[str, object]:
    level = min(max(level, 1), 3)
    key = f"heading_{level}"
    return {"object": "block", "type": key, key: {"rich_text": _rich_text(text)}}


def _paragraph(text: str) -> Dict[str, object]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": _rich_text(text)},
    }


def _bulleted(text: str) -> Dict[str, object]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _rich_text(text)},
    }


def _rich_text(text: str) -> List[Dict[str, object]]:
    return [{"type": "text", "text": {"content": text}}]


def _plain_text_property(prop: Mapping[str, Any] | None) -> str:
    if not prop:
        return ""

    prop_type = prop.get("type")
    if prop_type == "title" or prop_type == "rich_text":
        value = prop.get(prop_type) or []
        if isinstance(value, list):
            return "".join(part.get("plain_text", "") for part in value)

    if prop_type in {"select", "status"}:
        option = prop.get(prop_type) or {}
        if isinstance(option, dict):
            return str(option.get("name", ""))

    if prop_type == "multi_select":
        options = prop.get("multi_select") or []
        if isinstance(options, list):
            return ", ".join(str(opt.get("name", "")) for opt in options if isinstance(opt, dict))

    if prop_type == "url":
        return str(prop.get("url") or "")

    if prop_type == "number":
        number = prop.get("number")
        return "" if number is None else str(number)

    if prop_type == "formula":
        formula = prop.get("formula") or {}
        if isinstance(formula, dict):
            if "string" in formula:
                return str(formula.get("string") or "")
            if "number" in formula and formula.get("number") is not None:
                return str(formula.get("number"))

    return ""


def _pick_property(
    properties: Mapping[str, Any], candidates: Iterable[str]
) -> Mapping[str, Any] | None:
    for name in candidates:
        if name in properties:
            prop = properties[name]
            if isinstance(prop, dict):
                return prop
    return None


def _normalize_result(value: str) -> str:
    v = value.strip().lower()
    if not v:
        return ""

    if v in {"win", "victory", "w", "1-0"}:
        return "win"
    if v in {"loss", "lose", "l", "0-1"}:
        return "loss"
    if v in {"draw", "d", "1/2-1/2", "½"}:
        return "draw"

    if "win" in v:
        return "win"
    if "loss" in v or "defeat" in v:
        return "loss"
    if "draw" in v or "null" in v:
        return "draw"

    return v


@dataclass
class ChessGameRow:
    color: str
    result: str
    opening: str
    eco: str
    time_control: str


def _result_score(result: str) -> float:
    r = _normalize_result(result)
    if r == "win":
        return 1.0
    if r == "draw":
        return 0.5
    if r == "loss":
        return 0.0
    return 0.0


def _load_games_from_notion(
    database_id: str,
    *,
    notion: NotionService,
    color_fields: Sequence[str],
    result_fields: Sequence[str],
    opening_fields: Sequence[str],
    eco_fields: Sequence[str],
    time_control_fields: Sequence[str],
    max_games: int | None = None,
    filter_: Dict[str, Any] | None = None,
) -> List[ChessGameRow]:
    # On essaie de passer le filtre si le service le supporte (NotionService),
    # sinon on retombe sur l'appel simple (DummyNotionService des tests).
    try:
        if filter_ is not None:
            pages = notion.query_database(database_id, filter_=filter_)
        else:
            pages = notion.query_database(database_id)
    except TypeError:
        # Compatibilité avec les implémentations plus simples (DummyNotionService)
        pages = notion.query_database(database_id)

    games: List[ChessGameRow] = []

    for page in pages:
        properties = page.get("properties") or {}
        if not isinstance(properties, dict):
            continue

        color_prop = _pick_property(properties, color_fields)
        result_prop = _pick_property(properties, result_fields)
        opening_prop = _pick_property(properties, opening_fields)
        eco_prop = _pick_property(properties, eco_fields)
        tc_prop = _pick_property(properties, time_control_fields)

        color = _plain_text_property(color_prop)
        result = _plain_text_property(result_prop)
        opening = _plain_text_property(opening_prop)
        eco = _plain_text_property(eco_prop)
        time_control = _plain_text_property(tc_prop)

        if not result:
            continue

        games.append(
            ChessGameRow(
                color=color,
                result=result,
                opening=opening,
                eco=eco,
                time_control=time_control,
            )
        )

        if max_games is not None and len(games) >= max_games:
            break

    return games


def _aggregate_stats(games: Sequence[ChessGameRow]) -> Dict[str, Any]:
    total = len(games)
    wins = sum(1 for g in games if _normalize_result(g.result) == "win")
    draws = sum(1 for g in games if _normalize_result(g.result) == "draw")
    losses = sum(1 for g in games if _normalize_result(g.result) == "loss")
    winrate = (wins + 0.5 * draws) / total if total else 0.0

    by_color: Dict[str, Dict[str, Any]] = {}
    by_time: Dict[str, Dict[str, Any]] = {}
    by_opening: Dict[str, Dict[str, Any]] = {}

    for game in games:
        score = _result_score(game.result)
        norm_color = (game.color or "").lower() or "n/a"
        norm_tc = (game.time_control or "").lower() or "n/a"
        key_opening = game.opening or game.eco or "Unknown"

        for bucket, key in (
            (by_color, norm_color),
            (by_time, norm_tc),
            (by_opening, key_opening),
        ):
            data = bucket.setdefault(key, {"count": 0, "score": 0.0})
            data["count"] += 1
            data["score"] += score

    def _finalize(bucket: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        for key, data in bucket.items():
            raw_count = data.get("count", 0)
            raw_score = data.get("score", 0.0)

            count = int(raw_count) if isinstance(raw_count, (int, float)) else 0
            score = float(raw_score) if isinstance(raw_score, (int, float)) else 0.0

            data["count"] = count
            data["score"] = score
            data["winrate"] = score / count if count else 0.0

        return bucket

    return {
        "total": total,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "winrate": winrate,
        "by_color": _finalize(by_color),
        "by_time": _finalize(by_time),
        "by_opening": _finalize(by_opening),
    }


def _format_bucket(
    name: str, bucket: Mapping[str, Mapping[str, Any]], *, limit: int | None = None
) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = [_heading(name, level=3)]

    sorted_items = sorted(
        bucket.items(),
        key=lambda item: int(item[1].get("count", 0) or 0),
        reverse=True,
    )

    if limit is not None:
        sorted_items = sorted_items[:limit]

    for key, data in sorted_items:
        count = data.get("count", 0)
        winrate = data.get("winrate", 0.0)
        blocks.append(_bulleted(f"{key} — {count} parties, winrate {winrate:.1%}"))

    return blocks


def publish_chess_insights_from_notion(
    database_id: str,
    *,
    parent_page_id: str | None = None,
    notion_service: NotionService | None = None,
    top_openings: int = 5,
    max_games: int | None = None,
    since_days: int | None = None,
    color_fields: Sequence[str] = ("POV", "Color", "Side"),
    result_fields: Sequence[str] = ("Result", "Outcome"),
    opening_fields: Sequence[str] = ("Opening", "Opening Name"),
    eco_fields: Sequence[str] = ("ECO",),
    time_control_fields: Sequence[str] = ("Time Control", "Cadence", "TimeControl"),
) -> NotionPageRef:
    notion = notion_service or NotionService()

    # Ici, la fonction est volontairement stricte :
    # elle exige un parent explicite (les env sont gérés dans main()).
    parent = parent_page_id

    if not isinstance(parent, str) or not parent:
        raise ValueError("Aucun parent Notion fourni pour publier les insights.")

    # --- filtre "pro" sur la date des parties ---
    filter_: Dict[str, Any] | None = None
    if since_days is not None and since_days > 0:
        cutoff = date.today() - timedelta(days=since_days)
        cutoff_iso = cutoff.isoformat()
        filter_ = {
            "property": "Date",
            "date": {
                "on_or_after": cutoff_iso,
            },
        }

    games = _load_games_from_notion(
        database_id,
        notion=notion,
        color_fields=color_fields,
        result_fields=result_fields,
        opening_fields=opening_fields,
        eco_fields=eco_fields,
        time_control_fields=time_control_fields,
        max_games=max_games,
        filter_=filter_,
    )

    stats = _aggregate_stats(games)

    blocks: List[Dict[str, Any]] = [
        _heading("Chess.com — Insights", level=2),
        _paragraph(
            f"{stats['total']} parties, winrate global {stats['winrate']:.1%} "
            f"(W {stats['wins']} / D {stats['draws']} / L {stats['losses']})."
        ),
    ]

    blocks.extend(
        _format_bucket("Par couleur", stats["by_color"]),
    )
    blocks.extend(
        _format_bucket("Par cadence", stats["by_time"]),
    )
    blocks.extend(
        _format_bucket("Ouvertures les plus jouées", stats["by_opening"], limit=top_openings),
    )

    return notion.create_page_under_parent(
        title="Chess.com – Insights",
        blocks=blocks,
        parent_page_id=parent,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hanuman.orchestrations.chess_notion_insights",
        description="Synthétise les parties Chess.com stockées dans une base Notion.",
    )
    parser.add_argument(
        "--database-id",
        help="ID de la database Notion (sinon NOTION_CHESS_DB_ID).",
    )
    parser.add_argument(
        "--parent-page-id",
        help="Page Notion où publier le résumé (sinon NOTION_CHESS_PARENT_ID / NOTION_PARENT_PAGE_ID).",
    )
    parser.add_argument(
        "--top-openings",
        type=int,
        default=5,
        help="Nombre d'ouvertures à afficher dans le top (défaut: 5).",
    )
    parser.add_argument(
        "--max-games",
        type=int,
        default=None,
        help="Nombre max de parties à analyser (limite côté Python).",
    )
    parser.add_argument(
        "--since-days",
        type=int,
        default=None,
        help="Ne considérer que les parties dont la date est dans les N derniers jours.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    database_id = args.database_id or os.getenv("NOTION_CHESS_DB_ID")
    if not database_id:
        raise SystemExit(
            "Veuillez fournir --database-id ou définir NOTION_CHESS_DB_ID dans le .env"
        )

    parent = (
        args.parent_page_id
        or os.getenv("NOTION_CHESS_PARENT_ID")
        or os.getenv("NOTION_PARENT_PAGE_ID")
    )

    ref = publish_chess_insights_from_notion(
        database_id=database_id,
        parent_page_id=parent,
        notion_service=None,
        top_openings=args.top_openings,
        max_games=args.max_games,
        since_days=args.since_days,
    )

    print(f"[OK] Page d'insights créée: {ref.url} (id={ref.page_id})")


if __name__ == "__main__":
    main()
