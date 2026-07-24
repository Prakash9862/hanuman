from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_DEFAULT_EXCLUDED_DIRS = {".git", ".obsidian", ".trash", "node_modules"}


@dataclass(frozen=True)
class ObsidianNote:
    path: str
    title: str
    modified_at: str
    tags: list[str]
    size: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ObsidianService:
    """Connecteur interne vers un vault Obsidian local."""

    def __init__(self, vault_path: str | Path | None = None) -> None:
        configured = vault_path or os.environ.get("OBSIDIAN_VAULT_PATH")
        if not configured:
            raise RuntimeError("OBSIDIAN_VAULT_PATH manquant dans l'environnement")

        self.vault_path = Path(configured).expanduser().resolve()
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault Obsidian introuvable: {self.vault_path}")
        if not self.vault_path.is_dir():
            raise NotADirectoryError(f"Le vault Obsidian n'est pas un dossier: {self.vault_path}")

        configured_exclusions = os.environ.get("OBSIDIAN_EXCLUDED_DIRS", "")
        self.excluded_dirs = _DEFAULT_EXCLUDED_DIRS | {
            value.strip() for value in configured_exclusions.split(",") if value.strip()
        }

    def _resolve_note_path(self, relative_path: str | Path) -> Path:
        relative = Path(relative_path)
        if relative.is_absolute():
            raise ValueError("Le chemin d'une note doit être relatif au vault")

        resolved = (self.vault_path / relative).resolve()
        try:
            resolved.relative_to(self.vault_path)
        except ValueError as exc:
            raise ValueError("Le chemin demandé sort du vault Obsidian") from exc

        if resolved.suffix.lower() != ".md":
            raise ValueError("Seuls les fichiers Markdown .md sont autorisés")
        return resolved

    @staticmethod
    def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
        match = _FRONTMATTER_RE.match(text)
        if not match:
            return {}, text

        try:
            data = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            data = {}
        if not isinstance(data, dict):
            data = {}
        return data, text[match.end() :]

    @staticmethod
    def _normalise_tags(raw: Any) -> list[str]:
        if isinstance(raw, list):
            return [str(tag).strip() for tag in raw if str(tag).strip()]
        if isinstance(raw, str):
            return [tag.strip() for tag in raw.split(",") if tag.strip()]
        return []

    def list_notes(self) -> list[dict[str, Any]]:
        notes: list[ObsidianNote] = []
        for path in self.vault_path.rglob("*.md"):
            relative = path.relative_to(self.vault_path)
            if any(part in self.excluded_dirs or part.startswith(".") for part in relative.parts[:-1]):
                continue

            try:
                text = path.read_text(encoding="utf-8")
                frontmatter, _ = self._split_frontmatter(text)
                stat = path.stat()
            except (OSError, UnicodeError):
                continue

            notes.append(
                ObsidianNote(
                    path=relative.as_posix(),
                    title=str(frontmatter.get("title") or path.stem),
                    modified_at=datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                    tags=self._normalise_tags(frontmatter.get("tags")),
                    size=stat.st_size,
                )
            )

        notes.sort(key=lambda note: note.path.casefold())
        return [note.to_dict() for note in notes]

    def read_note(self, relative_path: str | Path) -> dict[str, Any]:
        path = self._resolve_note_path(relative_path)
        if not path.exists():
            raise FileNotFoundError(f"Note Obsidian introuvable: {relative_path}")

        text = path.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(text)
        return {
            "path": path.relative_to(self.vault_path).as_posix(),
            "absolute_path": str(path),
            "title": str(frontmatter.get("title") or path.stem),
            "frontmatter": frontmatter,
            "content": body,
        }

    def write_note(self, relative_path: str | Path, content: str, *, overwrite: bool = False) -> str:
        path = self._resolve_note_path(relative_path)
        if path.exists() and not overwrite:
            raise FileExistsError(f"La note existe déjà: {relative_path}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path.relative_to(self.vault_path).as_posix()
