from pathlib import Path

from hanuman.orchestrations.notion_markdown_sanitizer import (
    create_sanitized_markdown_copy,
    normalize_notion_code_language,
    sanitize_markdown_for_notion,
)


def test_language_normalization_handles_empty_alias_known_and_unknown():
    assert normalize_notion_code_language("") == "plain text"
    assert normalize_notion_code_language(" PY ") == "python"
    assert normalize_notion_code_language("Rust") == "rust"
    assert normalize_notion_code_language("made-up") == "plain text"


def test_sanitize_markdown_preserves_indent_and_normalizes_fences():
    markdown = "```py\nprint('x')\n```\n\n  ```unknown\nvalue\n  ```"
    assert sanitize_markdown_for_notion(markdown) == (
        "```python\nprint('x')\n```plain text\n" "  ```plain text\nvalue\n  ```plain text"
    )


def test_create_sanitized_copy_does_not_modify_source(tmp_path: Path):
    source = tmp_path / "note.md"
    source.write_text("```js\nalert(1)\n```", encoding="utf-8")

    copy = create_sanitized_markdown_copy(source)

    try:
        assert copy != source
        assert copy.read_text(encoding="utf-8") == "```javascript\nalert(1)\n```plain text"
        assert source.read_text(encoding="utf-8") == "```js\nalert(1)\n```"
    finally:
        copy.unlink()
