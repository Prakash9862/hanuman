from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProgramDefinition:
    id: str
    label: str
    candidates: tuple[str, ...]
    version_args: tuple[str, ...] = ("--version",)
    stdin: str | None = None


PROGRAMS: tuple[ProgramDefinition, ...] = (
    ProgramDefinition("stockfish", "Stockfish", ("stockfish", "/usr/games/stockfish"), (), "quit\n"),
    ProgramDefinition("scid", "SCID", ("scid", "/usr/games/scid"), ("--help",)),
    ProgramDefinition("lc0", "Leela Chess Zero", ("lc0", "leelaz"), ("--version",)),
    ProgramDefinition("ffmpeg", "FFmpeg", ("ffmpeg",), ("-version",)),
)


def _resolve(definition: ProgramDefinition) -> str | None:
    for candidate in definition.candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        path = Path(candidate)
        if path.is_file() and path.exists():
            return str(path)
    return None


def inspect_program(program_id: str) -> dict[str, Any]:
    definition = next((item for item in PROGRAMS if item.id == program_id), None)
    if definition is None:
        raise KeyError(program_id)

    executable = _resolve(definition)
    if not executable:
        return {
            "id": definition.id,
            "label": definition.label,
            "ok": False,
            "installed": False,
            "path": None,
            "version": None,
            "message": "Programme non installé",
        }

    version: str | None = None
    try:
        result = subprocess.run(
            [executable, *definition.version_args],
            input=definition.stdin,
            text=True,
            capture_output=True,
            timeout=4,
            check=False,
        )
        output = (result.stdout or result.stderr).strip().splitlines()
        version = output[0][:180] if output else None
    except (OSError, subprocess.SubprocessError):
        version = None

    return {
        "id": definition.id,
        "label": definition.label,
        "ok": True,
        "installed": True,
        "path": executable,
        "version": version,
        "message": "Programme disponible",
    }


def inspect_programs() -> list[dict[str, Any]]:
    return [inspect_program(item.id) for item in PROGRAMS]
