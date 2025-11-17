from __future__ import annotations

from typing import Dict, Iterable, List, Mapping

import pytest

from hanuman.orchestrations.chess_notion_insights import (
    ChessGameRow,
    _aggregate_stats,
    _load_games_from_notion,
    publish_chess_insights_from_notion,
)
from hanuman.services.core.notion_service import NotionPageRef, NotionService


class DummyNotionService(NotionService):
    def __init__(
        self, pages: List[Mapping[str, object]]
    ) -> None:  # pragma: no cover - init not used
        # Ne pas appeler le parent pour éviter la vérification du token
        self._pages = pages
        self.created: List[Dict[str, object]] = []

    def query_database(self, database_id: str):  # type: ignore[override]
        self.last_db = database_id
        return self._pages

    def create_page_under_parent(
        self, title: str, blocks: List[dict], parent_page_id: str | None = None
    ):  # type: ignore[override]
        ref = NotionPageRef(
            page_id=f"page-{len(self.created)}", url="https://notion.so/page"
        )
        self.created.append(
            {"title": title, "blocks": blocks, "parent": parent_page_id}
        )
        return ref


@pytest.fixture(autouse=True)
def patch_notion_init(monkeypatch: pytest.MonkeyPatch) -> Iterable[None]:
    monkeypatch.setattr(NotionService, "__init__", lambda self: None)
    yield


def _notion_page(properties: Mapping[str, object]) -> Dict[str, object]:
    return {"properties": properties}


def test_load_games_extracts_fields_from_various_property_types() -> None:
    pages = [
        _notion_page(
            {
                "POV": {"type": "select", "select": {"name": "White"}},
                "Result": {
                    "type": "rich_text",
                    "rich_text": [{"plain_text": "Win"}],
                },
                "Opening": {
                    "type": "title",
                    "title": [{"plain_text": "Sicilian"}],
                },
                "ECO": {"type": "rich_text", "rich_text": [{"plain_text": "B40"}]},
                "Time Control": {"type": "url", "url": "Blitz"},
            }
        ),
        _notion_page(
            {
                "Color": {"type": "select", "select": {"name": "Black"}},
                "Outcome": {"type": "status", "status": {"name": "Draw"}},
                "Opening Name": {
                    "type": "multi_select",
                    "multi_select": [{"name": "French"}],
                },
                "ECO": {"type": "number", "number": None},
                "Cadence": {
                    "type": "rich_text",
                    "rich_text": [{"plain_text": "Rapid"}],
                },
            }
        ),
    ]

    notion = DummyNotionService(pages)

    games = _load_games_from_notion(
        "db-1",
        notion=notion,
        color_fields=("POV", "Color"),
        result_fields=("Result", "Outcome"),
        opening_fields=("Opening", "Opening Name"),
        eco_fields=("ECO",),
        time_control_fields=("Time Control", "Cadence"),
    )

    assert notion.last_db == "db-1"
    assert games == [
        ChessGameRow(
            color="White",
            result="Win",
            opening="Sicilian",
            eco="B40",
            time_control="Blitz",
        ),
        ChessGameRow(
            color="Black",
            result="Draw",
            opening="French",
            eco="",
            time_control="Rapid",
        ),
    ]


def test_aggregate_stats_groups_by_color_time_and_opening() -> None:
    games = [
        ChessGameRow(
            color="White",
            result="Win",
            opening="Sicilian",
            eco="B40",
            time_control="Blitz",
        ),
        ChessGameRow(
            color="Black",
            result="Loss",
            opening="Sicilian",
            eco="B40",
            time_control="Blitz",
        ),
        ChessGameRow(
            color="White",
            result="Draw",
            opening="French",
            eco="C00",
            time_control="Rapid",
        ),
    ]

    stats = _aggregate_stats(games)

    assert stats["total"] == 3
    assert stats["wins"] == 1
    assert stats["draws"] == 1
    assert stats["losses"] == 1
    assert pytest.approx(stats["winrate"], rel=1e-4) == (1 + 0.5) / 3

    assert stats["by_color"]["white"]["count"] == 2
    assert (
        pytest.approx(stats["by_color"]["white"]["winrate"], rel=1e-4) == (1 + 0.5) / 2
    )
    assert stats["by_time"]["blitz"]["count"] == 2
    assert stats["by_opening"]["Sicilian"]["count"] == 2


def test_publish_chess_insights_from_notion_creates_summary_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pages = [
        _notion_page(
            {
                "POV": {"type": "select", "select": {"name": "White"}},
                "Result": {"type": "rich_text", "rich_text": [{"plain_text": "Win"}]},
                "Opening": {"type": "title", "title": [{"plain_text": "London"}]},
                "ECO": {"type": "rich_text", "rich_text": [{"plain_text": "D02"}]},
                "Time Control": {"type": "url", "url": "Rapid"},
            }
        )
    ]
    notion = DummyNotionService(pages)

    ref = publish_chess_insights_from_notion(
        "db-games",
        parent_page_id="parent-001",
        notion_service=notion,
        top_openings=1,
    )

    assert ref.page_id == "page-0"
    created = notion.created[0]
    assert created["parent"] == "parent-001"
    assert created["title"] == "Chess.com – Insights"
    paragraphs = [b for b in created["blocks"] if b.get("type") == "paragraph"]
    assert paragraphs, "Un paragraphe de résumé doit être présent"
    bullet_sections = [
        b for b in created["blocks"] if b.get("type") == "bulleted_list_item"
    ]
    assert bullet_sections, "Les stats agrégées doivent être formatées en liste"


def test_publish_chess_insights_from_notion_requires_parent() -> None:
    notion = DummyNotionService(
        [
            _notion_page(
                {"Result": {"type": "rich_text", "rich_text": [{"plain_text": "Win"}]}}
            )
        ]
    )

    with pytest.raises(ValueError, match="parent Notion"):
        publish_chess_insights_from_notion("db-id", notion_service=notion)
