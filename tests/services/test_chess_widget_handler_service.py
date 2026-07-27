from __future__ import annotations

from pathlib import Path

import pytest

from hanuman.services.chess_widget_handler_service import (
    ChessWidgetError,
    ChessWidgetHandler,
    parse_widget_uri,
    resolve_widget,
)

BOARD_ID = "hanuman-board-d00-main-test"
FEN = "r2qkbnr/ppp2ppp/2n1p3/3p1b2/2PP1B2/1Q2P3/PP3PPP/RN2KBNR b KQkq - 1 5"
PGN = '[Event "Test"]\n\n1. d4 d5 2. Bf4 Nc6 3. e3 Bf5 4. c4 e6 5. Qb3 *'


def _opening(root: Path) -> Path:
    path = root / "_Index" / "Ouvertures" / "eco_test4.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"""---
boards:
- id: {BOARD_ID}
  fen: {FEN}
  pgn: |
    {PGN.replace(chr(10), chr(10) + "    ")}
  eco: D00
  variant: main-line
  exit_move: Qb3
  games_count: 7
  player_color: white
  representative_note: 2026/01/game.md
---
""",
        encoding="utf-8",
    )
    note = root / "2026" / "01" / "game.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Game\n", encoding="utf-8")
    return path


def test_parse_and_resolve_real_widget_shape(tmp_path: Path) -> None:
    _opening(tmp_path)
    request = parse_widget_uri(f"hanuman://chess/boards/{BOARD_ID}?action=open-scid")
    widget = resolve_widget(tmp_path / "_Index" / "Ouvertures", request.board_id)
    assert request.action == "open-scid"
    assert widget.fen == FEN
    assert widget.pgn == PGN
    assert widget.games_count == 7


@pytest.mark.parametrize(
    "uri",
    [
        "https://chess/boards/id?action=open-scid",
        "hanuman://chess/games/id?action=open-scid",
        "hanuman://chess/boards/id",
    ],
)
def test_rejects_invalid_uri(uri: str) -> None:
    with pytest.raises(ChessWidgetError, match="URI Hanuman invalide"):
        parse_widget_uri(uri)


def test_unknown_widget_and_action_are_explicit(tmp_path: Path) -> None:
    _opening(tmp_path)
    handler = ChessWidgetHandler(
        chess_root=tmp_path,
        vault_name="Vault",
        cache_dir=tmp_path / "cache",
        state_dir=tmp_path / "state",
    )
    with pytest.raises(ChessWidgetError, match="Widget inconnu"):
        handler.handle("hanuman://chess/boards/unknown?action=copy-fen")
    with pytest.raises(ChessWidgetError, match="Action inconnue"):
        handler.handle(f"hanuman://chess/boards/{BOARD_ID}?action=explode")


def test_open_scid_writes_exact_fen_pgn(tmp_path: Path, monkeypatch) -> None:
    _opening(tmp_path)
    calls: list[list[str]] = []

    class Process:
        pid = 123

    monkeypatch.setattr(
        "hanuman.services.chess_widget_handler_service.shutil.which",
        lambda name: "/usr/games/scid" if name == "scid" else None,
    )
    monkeypatch.setattr(
        "hanuman.services.chess_widget_handler_service.subprocess.Popen",
        lambda command, **kwargs: calls.append(command) or Process(),
    )
    handler = ChessWidgetHandler(
        chess_root=tmp_path,
        vault_name="Vault",
        cache_dir=tmp_path / "cache",
        state_dir=tmp_path / "state",
    )
    handler.handle(f"hanuman://chess/boards/{BOARD_ID}?action=open-scid")
    generated = (tmp_path / "cache" / f"{BOARD_ID}.pgn").read_text(encoding="utf-8")
    assert f'[FEN "{FEN}"]' in generated
    assert '[SetUp "1"]' in generated
    assert calls == [["/usr/games/scid", str(tmp_path / "cache" / f"{BOARD_ID}.pgn")]]


def test_obsidian_actions_use_real_notes(tmp_path: Path, monkeypatch) -> None:
    source = _opening(tmp_path)
    opened: list[str] = []
    handler = ChessWidgetHandler(
        chess_root=tmp_path,
        vault_name="Mon Vault",
        cache_dir=tmp_path / "cache",
        state_dir=tmp_path / "state",
    )
    monkeypatch.setattr(handler, "_open_uri", lambda uri: opened.append(uri) or uri)
    handler.handle(f"hanuman://chess/boards/{BOARD_ID}?action=open-games")
    handler.handle(f"hanuman://chess/boards/{BOARD_ID}?action=open-note")
    assert source.stem in opened[0]
    assert "%23%F0%9F%97%82%EF%B8%8F%20Parties" in opened[0]
    assert "2026/01/game" in opened[1]


def test_stockfish_action_is_honestly_unavailable(tmp_path: Path) -> None:
    _opening(tmp_path)
    handler = ChessWidgetHandler(
        chess_root=tmp_path,
        vault_name="Vault",
        cache_dir=tmp_path / "cache",
        state_dir=tmp_path / "state",
    )
    with pytest.raises(ChessWidgetError, match="aucun moteur n'est configuré"):
        handler.handle(f"hanuman://chess/boards/{BOARD_ID}?action=open-stockfish")
