from __future__ import annotations

from hanuman.services.core.contacts_service import ping_contacts


def test_ping_contacts_returns_available_status() -> None:
    status = ping_contacts()

    assert status.ok is True
    assert status.configured is True
    assert status.message is None
