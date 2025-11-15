from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

import hanuman.api.core.obsidian as obsidian_api
from hanuman.main import app

client = TestClient(app)


def _fake_abs_path(stem_value: str) -> SimpleNamespace:
    return SimpleNamespace(stem=stem_value)


def test_obsidian_sync_one_success(monkeypatch) -> None:
    monkeypatch.setattr(obsidian_api, "read_markdown", lambda path: "# Title")
    monkeypatch.setattr(obsidian_api, "md_title", lambda md, fallback: "Computed Title")
    monkeypatch.setattr(
        obsidian_api, "md_to_blocks", lambda md: [{"type": "paragraph"}]
    )
    monkeypatch.setattr(
        obsidian_api, "abs_path", lambda path: _fake_abs_path("fallback")
    )
    monkeypatch.setattr(
        obsidian_api,
        "create_page_under_parent",
        lambda title, blocks, parent_page_id=None: {
            "url": "https://notion",
            "id": "page-id",
        },
    )

    response = client.post("/obsidian/sync_one", json={"path": "note.md"})
    data = response.json()

    assert response.status_code == 200
    assert data["ok"] is True
    assert data["title"] == "Computed Title"
    assert data["url"] == "https://notion"
    assert data["id"] == "page-id"


def test_obsidian_sync_one_custom_title(monkeypatch) -> None:
    monkeypatch.setattr(obsidian_api, "read_markdown", lambda path: "# Title")
    monkeypatch.setattr(
        obsidian_api, "md_title", lambda md, fallback: "Should not be used"
    )
    monkeypatch.setattr(
        obsidian_api, "md_to_blocks", lambda md: [{"type": "paragraph"}]
    )
    monkeypatch.setattr(
        obsidian_api, "abs_path", lambda path: _fake_abs_path("fallback")
    )
    monkeypatch.setattr(
        obsidian_api,
        "create_page_under_parent",
        lambda title, blocks, parent_page_id=None: {
            "url": "https://notion",
            "id": "page-id",
        },
    )

    response = client.post(
        "/obsidian/sync_one",
        json={"path": "note.md", "title": "Custom Title", "parent_page_id": "parent"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["title"] == "Custom Title"


def test_obsidian_sync_one_failure(monkeypatch) -> None:
    def failing_read(path: str) -> str:  # pragma: no cover - helper
        raise ValueError("missing note")

    monkeypatch.setattr(obsidian_api, "read_markdown", failing_read)

    response = client.post("/obsidian/sync_one", json={"path": "missing.md"})

    assert response.status_code == 400
    assert "sync_one failed" in response.json()["detail"]


def test_obsidian_sync_many(monkeypatch) -> None:
    def fake_read(path: str) -> str:
        if path == "good.md":
            return "# Good"
        raise RuntimeError("boom")

    def fake_md_title(md: str, fallback: str) -> str:
        return f"title:{fallback}"

    def fake_md_to_blocks(md: str) -> list[dict]:
        return [{"type": "paragraph", "text": md}]

    def fake_create_page(title: str, blocks: list[dict], parent_page_id=None) -> dict:
        return {"url": f"https://notion/{title}", "id": "id"}

    monkeypatch.setattr(obsidian_api, "read_markdown", fake_read)
    monkeypatch.setattr(obsidian_api, "md_title", fake_md_title)
    monkeypatch.setattr(obsidian_api, "md_to_blocks", fake_md_to_blocks)
    monkeypatch.setattr(
        obsidian_api, "abs_path", lambda path: _fake_abs_path(path.split(".")[0])
    )
    monkeypatch.setattr(obsidian_api, "create_page_under_parent", fake_create_page)

    response = client.post(
        "/obsidian/sync_many",
        json={"paths": ["good.md", "bad.md"], "parent_page_id": "parent"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "partial"
    assert len(data["results"]) == 2
    assert data["results"][0]["ok"] is True
    assert data["results"][1]["ok"] is False
    assert data["results"][1]["err"] == "boom"
