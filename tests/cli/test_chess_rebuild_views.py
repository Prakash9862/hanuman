import hashlib
from pathlib import Path

import pytest

from hanuman.orchestrations import chess_rebuild_views as mod
from hanuman.services.chess_analysis_service import StockfishAnalyzer
from hanuman.services.core.chess_service import ChessService


def _note(game_id: str = "g1") -> str:
    return f"""---
type: chess-game
date: 2024-01-02
game_id: "{game_id}"
result: win
color: white
opponent: "Adversaire"
white: "Joueur"
black: "Adversaire"
eco: B20
opening: "Défense sicilienne"
time_control: "blitz"
chess_url: "https://example.test/game"
---

# Partie

PGN, analyse et notes humaines immuables.
"""


def _vault(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "preview"
    note = root / "2024/01/2024-01-02 - B20 - Adversaire.md"
    note.parent.mkdir(parents=True)
    note.write_text(_note(), encoding="utf-8")
    return root, note


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_vault_path_is_required() -> None:
    with pytest.raises(SystemExit) as exc:
        mod.main([])
    assert exc.value.code == 2


@pytest.mark.parametrize("raw", ["/", ""])
def test_unsafe_root_or_empty_path_is_refused(raw: str) -> None:
    with pytest.raises(mod.UnsafeChessVaultPathError):
        mod.validate_chess_vault_path(raw)


def test_missing_path_and_file_are_refused(tmp_path: Path) -> None:
    with pytest.raises(mod.UnsafeChessVaultPathError, match="n’existe pas"):
        mod.validate_chess_vault_path(str(tmp_path / "missing"))
    file_path = tmp_path / "file"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(mod.UnsafeChessVaultPathError, match="pas un dossier"):
        mod.validate_chess_vault_path(str(file_path))


def test_symbolic_vault_root_is_refused(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    symbolic_root = tmp_path / "symbolic"
    real_root.mkdir()
    symbolic_root.symlink_to(real_root, target_is_directory=True)

    with pytest.raises(mod.UnsafeChessVaultPathError, match="lien symbolique"):
        mod.validate_chess_vault_path(str(symbolic_root))


def test_home_and_repository_paths_are_refused() -> None:
    with pytest.raises(mod.UnsafeChessVaultPathError, match="personnel"):
        mod.validate_chess_vault_path(str(Path.home()))
    repository = Path(mod.__file__).resolve().parents[3]
    with pytest.raises(mod.UnsafeChessVaultPathError, match="dépôt"):
        mod.validate_chess_vault_path(str(repository))


def test_command_rebuilds_views_reports_and_preserves_every_source(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, note = _vault(tmp_path)
    legacy = root / "_Index/Annees/sentinel.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("legacy", encoding="utf-8")
    human = root / "_Index/Profil échiquéen.md"
    human.write_text("profil humain sans marqueurs", encoding="utf-8")
    before = {path: _digest(path) for path in (note, legacy, human)}

    assert mod.main(["--vault-path", str(root)]) == 0
    first_output = capsys.readouterr().out
    first_files = {
        path.relative_to(root): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    assert mod.main(["--vault-path", str(root)]) == 0
    second_output = capsys.readouterr().out
    second_files = {
        path.relative_to(root): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }

    assert '"notes_discovered": 1' in first_output
    assert '"notes_usable": 1' in first_output
    assert '"human_files_protected": 1' in first_output
    assert '"insight_blocks_absent": 1' in first_output
    assert first_output == second_output
    assert first_files == second_files
    assert {path: _digest(path) for path in before} == before
    assert (root / "_Index/Dashboard.md").is_file()
    assert (root / "_Index/Ouvertures/B20.md").is_file()
    assert not (root / "_Index/Annees/B20.md").exists()


def test_command_never_calls_chess_com_or_stockfish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _ = _vault(tmp_path)

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Dépendance externe interdite pendant rebuild-views.")

    monkeypatch.setattr(ChessService, "get_latest_games", forbidden)
    monkeypatch.setattr(StockfishAnalyzer, "__init__", forbidden)

    assert mod.main(["--vault-path", str(root)]) == 0
    assert '"notes_usable": 1' in capsys.readouterr().out


def test_business_error_is_readable_and_does_not_show_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _ = _vault(tmp_path)
    profile = root / "_Index/Profil échiquéen.md"
    profile.parent.mkdir(parents=True)
    profile.write_text(
        "<!-- HANUMAN:GENERATED:START -->\nzone incomplète",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exc:
        mod.main(["--vault-path", str(root)])

    assert exc.value.code == 2
    error = capsys.readouterr().err
    assert "Erreur de reconstruction Chess" in error
    assert "Traceback" not in error


def test_parser_exposes_no_destructive_option() -> None:
    help_text = mod.build_parser().format_help()
    assert "--reset" not in help_text
    assert "--clean" not in help_text
    assert "--delete" not in help_text


def test_command_refuses_index_symlink_without_writing_outside(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _ = _vault(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "_Index").symlink_to(outside, target_is_directory=True)

    with pytest.raises(SystemExit) as exc:
        mod.main(["--vault-path", str(root)])

    assert exc.value.code == 2
    assert list(outside.iterdir()) == []
    assert "symbolique" in capsys.readouterr().err
