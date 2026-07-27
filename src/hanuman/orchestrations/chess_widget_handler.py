from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from hanuman.services.chess_widget_handler_service import (
    ChessWidgetError,
    ChessWidgetHandler,
)

DEFAULT_CHESS_ROOT = Path("/home/vince/Prakash/projets/Obsidian_Priv-/Echecs")
DEFAULT_VAULT_NAME = "Obsidian_Priv-"


def _configure_logging() -> Path:
    state_dir = Path.home() / ".local" / "state" / "hanuman"
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path = state_dir / "chess-widget-handler.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return log_path


def _notify(message: str) -> None:
    try:
        subprocess.Popen(
            ["notify-send", "Hanuman · Échecs", message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    _configure_logging()
    if len(args) != 1:
        message = "Une URI hanuman:// est requise."
        logging.error(message)
        _notify(message)
        return 2
    chess_root = Path(os.environ.get("HANUMAN_CHESS_ROOT", DEFAULT_CHESS_ROOT))
    vault_name = os.environ.get("HANUMAN_VAULT_NAME", DEFAULT_VAULT_NAME)
    try:
        result = ChessWidgetHandler(chess_root=chess_root, vault_name=vault_name).handle(args[0])
    except ChessWidgetError as exc:
        logging.error("%s", exc)
        _notify(str(exc))
        print(str(exc), file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
