from __future__ import annotations

import logging
import os
import shutil
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

import chess
import chess.pgn
import yaml


class ChessWidgetError(RuntimeError):
    """Erreur compréhensible lors de l'exécution d'une action de widget."""


@dataclass(frozen=True)
class ChessWidget:
    board_id: str
    fen: str
    pgn: str
    eco: str
    variant: str
    exit_move: str
    games_count: int
    player_color: str
    representative_note: str
    source_note: Path


@dataclass(frozen=True)
class WidgetRequest:
    board_id: str
    action: str


def parse_widget_uri(uri: str) -> WidgetRequest:
    parsed = urlparse(uri)
    parts = [unquote(part) for part in parsed.path.split("/") if part]
    actions = parse_qs(parsed.query).get("action", [])
    if (
        parsed.scheme != "hanuman"
        or parsed.netloc != "chess"
        or len(parts) != 2
        or parts[0] != "boards"
        or len(actions) != 1
        or not parts[1]
    ):
        raise ChessWidgetError("URI Hanuman invalide.")
    return WidgetRequest(board_id=parts[1], action=actions[0])


def _frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    loaded = yaml.safe_load(text[4:end])
    return loaded if isinstance(loaded, dict) else {}


def resolve_widget(openings_dir: Path, board_id: str) -> ChessWidget:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(openings_dir.glob("*.md")):
        boards = _frontmatter(path).get("boards", [])
        if not isinstance(boards, list):
            continue
        for board in boards:
            if isinstance(board, dict) and board.get("id") == board_id:
                matches.append((path, board))
    if not matches:
        raise ChessWidgetError(f"Widget inconnu : {board_id}")
    if len(matches) > 1:
        raise ChessWidgetError(f"Identifiant de widget dupliqué : {board_id}")

    source_note, data = matches[0]
    fen = str(data.get("fen", "")).strip()
    pgn = str(data.get("pgn", "")).strip()
    try:
        chess.Board(fen)
    except ValueError as exc:
        raise ChessWidgetError(f"FEN absent ou invalide pour {board_id}.") from exc
    if not pgn:
        raise ChessWidgetError(f"PGN absent pour {board_id}.")

    return ChessWidget(
        board_id=board_id,
        fen=fen,
        pgn=pgn,
        eco=str(data.get("eco", "")),
        variant=str(data.get("variant", "")),
        exit_move=str(data.get("exit_move", "")),
        games_count=int(data.get("games_count", 0)),
        player_color=str(data.get("player_color", "")),
        representative_note=str(data.get("representative_note", "")),
        source_note=source_note,
    )


class ChessWidgetHandler:
    def __init__(
        self,
        *,
        chess_root: Path,
        vault_name: str,
        cache_dir: Path | None = None,
        state_dir: Path | None = None,
    ) -> None:
        self.chess_root = chess_root
        self.vault_name = vault_name
        self.openings_dir = chess_root / "_Index" / "Ouvertures"
        self.cache_dir = cache_dir or Path.home() / ".cache" / "hanuman" / "chess-widgets"
        self.state_dir = state_dir or Path.home() / ".local" / "state" / "hanuman"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("hanuman.chess_widget")

    def handle(self, uri: str) -> str:
        request = parse_widget_uri(uri)
        widget = resolve_widget(self.openings_dir, request.board_id)
        actions = {
            "open-scid": self.open_scid,
            "open-stockfish": self.open_stockfish,
            "open-games": self.open_games,
            "copy-fen": lambda item: self.copy_text(item, item.fen, "FEN"),
            "copy-pgn": lambda item: self.copy_text(item, item.pgn, "PGN"),
            "open-note": self.open_note,
        }
        action = actions.get(request.action)
        if action is None:
            raise ChessWidgetError(f"Action inconnue : {request.action}")
        result = action(widget)
        self.logger.info("action=%s board_id=%s result=%s", request.action, widget.board_id, result)
        return result

    def _scid_path(self) -> str:
        path = shutil.which("scid")
        if path is None and Path("/usr/games/scid").is_file():
            path = "/usr/games/scid"
        if path is None:
            raise ChessWidgetError("SCID est introuvable.")
        return path

    def _position_pgn(self, widget: ChessWidget) -> Path:
        path = self.cache_dir / f"{widget.board_id}.pgn"
        tags = {
            "Event": "Hanuman Chess Widget",
            "Site": "Hanuman",
            "Result": "*",
            "SetUp": "1",
            "FEN": widget.fen,
            "ECO": widget.eco,
            "HanumanBoardId": widget.board_id,
            "HanumanVariant": widget.variant,
            "HanumanExitMove": widget.exit_move,
            "HanumanGames": str(widget.games_count),
            "HanumanColor": widget.player_color,
        }

        def escaped(value: str) -> str:
            return value.replace("\\", "\\\\").replace('"', '\\"')

        content = "\n".join(f'[{key} "{escaped(value)}"]' for key, value in tags.items())
        path.write_text(f"{content}\n\n*\n", encoding="utf-8")
        return path

    def open_scid(self, widget: ChessWidget) -> str:
        pgn_path = self._position_pgn(widget)
        process = subprocess.Popen(
            [self._scid_path(), str(pgn_path)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return f"SCID lancé (pid={process.pid}) avec {pgn_path}"

    def open_stockfish(self, widget: ChessWidget) -> str:
        del widget
        raise ChessWidgetError(
            "Stockfish est installé, mais aucun moteur n'est configuré dans SCID 4.7.4."
        )

    def _obsidian_uri(self, relative_path: str, *, heading: str | None = None) -> str:
        target = relative_path.removesuffix(".md")
        if heading:
            target = f"{target}#{heading}"
        return (
            f"obsidian://open?vault={quote(self.vault_name, safe='')}"
            f"&file={quote(target, safe='/')}"
        )

    def _open_uri(self, uri: str) -> str:
        obsidian = Path("/opt/Obsidian/obsidian")
        if obsidian.is_file():
            command = [str(obsidian), uri]
        else:
            opener = shutil.which("xdg-open")
            if opener is None:
                raise ChessWidgetError("Obsidian et xdg-open sont introuvables.")
            command = [opener, uri]
        process = subprocess.Popen(
            command,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return f"URI ouverte (pid={process.pid}) : {uri}"

    def open_games(self, widget: ChessWidget) -> str:
        relative = widget.source_note.relative_to(self.chess_root.parent).as_posix()
        return self._open_uri(self._obsidian_uri(relative, heading="🗂️ Parties"))

    def open_note(self, widget: ChessWidget) -> str:
        if not widget.representative_note:
            raise ChessWidgetError("Aucune note représentative n'est définie.")
        note = self.chess_root / widget.representative_note
        if not note.is_file():
            raise ChessWidgetError("La note représentative est introuvable.")
        relative = note.relative_to(self.chess_root.parent).as_posix()
        return self._open_uri(self._obsidian_uri(relative))

    def copy_text(self, widget: ChessWidget, text: str, label: str) -> str:
        wish = shutil.which("wish")
        if wish is None or not os.environ.get("DISPLAY"):
            raise ChessWidgetError("Le presse-papiers X11 n'est pas accessible.")
        text_path = self.cache_dir / f"{widget.board_id}-{label.lower()}.txt"
        text_path.write_text(text, encoding="utf-8")
        pid_path = self.state_dir / "clipboard-owner.pid"
        self._stop_previous_clipboard_owner(pid_path)
        script = (
            "wm withdraw .\n"
            f"set f [open {{{text_path}}} r]\n"
            "set value [read $f]\n"
            "close $f\n"
            "clipboard clear\n"
            "clipboard append -- $value\n"
            "update\n"
            "vwait forever\n"
        )
        process = subprocess.Popen(
            [wish],
            stdin=subprocess.PIPE,
            text=True,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assert process.stdin is not None
        process.stdin.write(script)
        process.stdin.close()
        pid_path.write_text(str(process.pid), encoding="ascii")
        return f"{label} copié dans le presse-papiers."

    @staticmethod
    def _stop_previous_clipboard_owner(pid_path: Path) -> None:
        try:
            pid = int(pid_path.read_text(encoding="ascii"))
            command = Path(f"/proc/{pid}/comm").read_text(encoding="utf-8").strip()
            if command in {"wish", "wish8.6"}:
                os.kill(pid, signal.SIGTERM)
        except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
            pass
