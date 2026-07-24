from __future__ import annotations

import re
from pathlib import Path
from tempfile import NamedTemporaryFile

# Valeurs acceptées par l'API Notion pour les blocs de code.
# Les alias courants sont normalisés ; tout langage inconnu devient plain text.
NOTION_CODE_LANGUAGES = {
    "abap",
    "abc",
    "agda",
    "arduino",
    "ascii art",
    "assembly",
    "bash",
    "basic",
    "bnf",
    "c",
    "c#",
    "c++",
    "clojure",
    "coffeescript",
    "coq",
    "css",
    "dart",
    "dhall",
    "diff",
    "docker",
    "ebnf",
    "elixir",
    "elm",
    "erlang",
    "f#",
    "flow",
    "fortran",
    "gherkin",
    "glsl",
    "go",
    "graphql",
    "groovy",
    "haskell",
    "hcl",
    "html",
    "idris",
    "java",
    "javascript",
    "json",
    "julia",
    "kotlin",
    "latex",
    "less",
    "lisp",
    "livescript",
    "llvm ir",
    "lua",
    "makefile",
    "markdown",
    "markup",
    "matlab",
    "mathematica",
    "mermaid",
    "nix",
    "notion formula",
    "objective-c",
    "ocaml",
    "pascal",
    "perl",
    "php",
    "plain text",
    "powershell",
    "prolog",
    "protobuf",
    "purescript",
    "python",
    "r",
    "racket",
    "reason",
    "ruby",
    "rust",
    "sass",
    "scala",
    "scheme",
    "scss",
    "shell",
    "solidity",
    "sql",
    "swift",
    "toml",
    "typescript",
    "vb.net",
    "verilog",
    "vhdl",
    "visual basic",
    "webassembly",
    "xml",
    "yaml",
    "java/c/c++/c#",
}

LANGUAGE_ALIASES = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "sh": "shell",
    "zsh": "shell",
    "md": "markdown",
    "yml": "yaml",
    "text": "plain text",
    "txt": "plain text",
    "pgn": "plain text",
    "fen": "plain text",
    "stockfish": "plain text",
    "lichess": "plain text",
}

FENCE_RE = re.compile(r"^(?P<indent>\s*)```(?P<language>[^\s`]*)\s*$", re.MULTILINE)


def normalize_notion_code_language(language: str) -> str:
    normalized = language.strip().lower()
    if not normalized:
        return "plain text"
    normalized = LANGUAGE_ALIASES.get(normalized, normalized)
    return normalized if normalized in NOTION_CODE_LANGUAGES else "plain text"


def sanitize_markdown_for_notion(markdown: str) -> str:
    def replace(match: re.Match[str]) -> str:
        language = normalize_notion_code_language(match.group("language"))
        return f'{match.group("indent")}```{language}'

    return FENCE_RE.sub(replace, markdown)


def create_sanitized_markdown_copy(source: Path) -> Path:
    sanitized = sanitize_markdown_for_notion(source.read_text(encoding="utf-8"))
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".md",
        prefix=f"hanuman-{source.stem}-",
        delete=False,
    ) as handle:
        handle.write(sanitized)
        return Path(handle.name)
