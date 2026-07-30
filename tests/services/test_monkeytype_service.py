from __future__ import annotations

from hanuman.services.core.monkeytype_service import ping_monkeytype


def test_ping_monkeytype_returns_available_status() -> None:
    status = ping_monkeytype()

    assert status.ok is True
    assert status.configured is True
    assert status.message is None
