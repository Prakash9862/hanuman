from __future__ import annotations

from hanuman.services.core.devdocs_service import ping_devdocs


def test_ping_devdocs_returns_available_status() -> None:
    status = ping_devdocs()

    assert status.ok is True
    assert status.configured is True
    assert status.message is None
