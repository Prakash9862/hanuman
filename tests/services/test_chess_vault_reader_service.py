from pathlib import Path

from hanuman.services.chess_vault_reader_service import (
    read_chess_game_note,
    read_chess_vault,
)


def _note(
    *,
    date: str = "2024-01-02",
    color: str = "white",
    opening: str = '"Défense sicilienne"',
) -> str:
    return f"""---
type: chess-game
date: {date}
game_id: "g:échec"
result: win
color: {color}
opponent: "Adversaire"
white: "Joueur"
black: "Adversaire"
eco: B20
opening: {opening}
time_control: "blitz"
chess_url: "https://example.test/game"
---

# Partie
"""


def _write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_reads_complete_quoted_unicode_note_without_modifying_it(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    path = _write(root, "2024/01/2024-01-02 - B20 - Adversaire.md", _note())
    before = path.read_bytes()

    game = read_chess_game_note(root, path)

    assert game is not None
    assert game.game_id == "g:échec"
    assert game.opening_name == "Défense sicilienne"
    assert game.url == "https://example.test/game"
    assert game.pgn == ""
    assert path.read_bytes() == before


def test_ignores_note_without_frontmatter_and_non_chess_note(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    no_frontmatter = _write(root, "2024/01/sans frontmatter.md", "# Texte")
    other = _write(
        root,
        "2024/01/autre.md",
        "---\ntype: journal\ndate: 2024-01-01\n---\n",
    )

    result = read_chess_vault(root)

    assert result.notes_discovered == 2
    assert result.notes_usable == 0
    assert result.notes_ignored == 2
    assert {item.path for item in result.ignored_notes} == {no_frontmatter, other}


def test_reports_incomplete_invalid_date_color_and_path(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    _write(root, "2024/01/incomplete.md", "---\ntype: chess-game\n---\n")
    _write(
        root,
        "2024/01/bad-date.md",
        _note(date="02/01/2024"),
    )
    _write(root, "2024/01/bad-color.md", _note(color="red"))
    _write(root, "2024/01/wrong-name.md", _note())

    result = read_chess_vault(root)

    assert result.notes_usable == 0
    assert result.notes_ignored == 4
    reasons = "\n".join(item.reason for item in result.ignored_notes)
    assert reasons.count("Date Chess invalide") == 2
    assert "Date Chess invalide" in reasons
    assert "Couleur Chess invalide" in reasons
    assert "chemin ne correspond pas" in reasons


def test_read_order_is_deterministic_and_newest_first(tmp_path: Path) -> None:
    root = tmp_path / "Echecs"
    first = _note(date="2024-01-01").replace('"g:échec"', '"g1"')
    second = _note(date="2024-01-02").replace('"g:échec"', '"g2"')
    _write(root, "2024/01/2024-01-01 - B20 - Adversaire.md", first)
    _write(root, "2024/01/2024-01-02 - B20 - Adversaire.md", second)

    one = read_chess_vault(root)
    two = read_chess_vault(root)

    assert [game.game_id for game in one.games] == ["g2", "g1"]
    assert one == two
