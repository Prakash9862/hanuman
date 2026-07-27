from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from hanuman.services import local_programs_service as service


def test_resolve_prefers_executable_found_on_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition = service.ProgramDefinition("tool", "Tool", ("tool",))
    monkeypatch.setattr(service.shutil, "which", lambda candidate: "/usr/bin/tool")

    assert service._resolve(definition) == "/usr/bin/tool"


def test_resolve_returns_none_when_no_candidate_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition = service.ProgramDefinition("tool", "Tool", ("/missing/tool",))
    monkeypatch.setattr(service.shutil, "which", lambda candidate: None)

    assert service._resolve(definition) is None


def test_resolve_uses_path_candidate_when_which_finds_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable = tmp_path / "tool"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    definition = service.ProgramDefinition("tool", "Tool", (str(executable),))
    monkeypatch.setattr(service.shutil, "which", lambda candidate: None)

    assert service._resolve(definition) == str(executable)


def test_inspect_program_rejects_unknown_program() -> None:
    with pytest.raises(KeyError, match="unknown"):
        service.inspect_program("unknown")


def test_inspect_program_reports_missing_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service, "_resolve", lambda definition: None)

    result = service.inspect_program("ffmpeg")

    assert result["ok"] is False
    assert result["installed"] is False
    assert result["message"] == "Programme non installé"


def test_inspect_program_reads_first_version_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(service, "_resolve", lambda definition: "/usr/bin/ffmpeg")

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        captured.update(kwargs)
        return SimpleNamespace(stdout="ffmpeg version 7.0\nextra\n", stderr="")

    monkeypatch.setattr(service.subprocess, "run", fake_run)

    result = service.inspect_program("ffmpeg")

    assert captured["command"] == ["/usr/bin/ffmpeg", "-version"]
    assert captured["timeout"] == 4
    assert result["version"] == "ffmpeg version 7.0"
    assert result["ok"] is True


def test_inspect_program_tolerates_version_probe_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service, "_resolve", lambda definition: "/usr/bin/lc0")
    monkeypatch.setattr(
        service.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("lc0", 4)),
    )

    result = service.inspect_program("lc0")

    assert result["installed"] is True
    assert result["version"] is None


def test_inspect_program_skips_probe_when_program_has_no_version_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service, "_resolve", lambda definition: "/usr/bin/scid")
    monkeypatch.setattr(
        service.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("SCID must not be executed"),
    )

    result = service.inspect_program("scid")

    assert result["path"] == "/usr/bin/scid"
    assert result["version"] is None


def test_inspect_programs_preserves_registry_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []

    def fake_inspect(program_id: str) -> dict[str, str]:
        seen.append(program_id)
        return {"id": program_id}

    monkeypatch.setattr(service, "inspect_program", fake_inspect)

    assert service.inspect_programs() == [{"id": item.id} for item in service.PROGRAMS]
    assert seen == [item.id for item in service.PROGRAMS]
