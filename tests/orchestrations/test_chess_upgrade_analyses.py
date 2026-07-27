from pathlib import Path

from hanuman.models.chess_insight import ChessInsightEnvelope
from hanuman.orchestrations import chess_upgrade_analyses as mod
from hanuman.services.chess_insight_storage_service import render_insight_block


class FakeStockfishAnalyzer:
    def __init__(self, config) -> None:
        self.config = config

    def __enter__(self):
        return self

    def __exit__(self, *_: object) -> None:
        return None


def test_upgrade_skips_v2_and_limits_pending_without_touching_current(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "Echecs"
    paths = [root / "2026/01/a.md", root / "2026/01/b.md", root / "2026/01/c.md"]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("V1", encoding="utf-8")
    paths[0].write_text(
        render_insight_block(
            ChessInsightEnvelope(
                schema_version=2,
                game_id="a",
                eco="D00",
                insights=(),
                analysis_metadata={},
                opening_exit=None,
            )
        ),
        encoding="utf-8",
    )
    current_before = paths[0].read_bytes()
    analysed: list[Path] = []

    monkeypatch.setattr(mod, "_game_paths", lambda selected: paths)
    monkeypatch.setattr(mod, "StockfishAnalyzer", FakeStockfishAnalyzer)

    def fake_analyse(path: Path, analyzer, *, root: Path):
        analysed.append(path)
        return object()

    monkeypatch.setattr(mod, "analyse_note", fake_analyse)

    report = mod.upgrade_analyses(root=root, limit=1, depth=8)

    assert report["analysed"] == 1
    assert report["already_current"] == 1
    assert report["skipped"] == 1
    assert analysed == [paths[1]]
    assert paths[0].read_bytes() == current_before
