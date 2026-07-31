from __future__ import annotations

from unittest.mock import Mock, patch

from hanuman.services.connectors.contacts import ContactsConnectorError
from hanuman.services.core.contacts_service import ping_contacts


def test_ping_contacts_returns_connected_status() -> None:
    connector = Mock()
    connector.configured.return_value = True
    connector.list_contacts.return_value = Mock()

    with patch(
        "hanuman.services.core.contacts_service._connector",
        return_value=connector,
    ):
        status = ping_contacts()

    assert status.ok is True
    assert status.configured is True
    assert status.connected is True
    assert status.message is None


def test_ping_contacts_returns_not_configured_status() -> None:
    connector = Mock()
    connector.configured.return_value = False

    with patch(
        "hanuman.services.core.contacts_service._connector",
        return_value=connector,
    ):
        status = ping_contacts()

    assert status.ok is False
    assert status.configured is False
    assert status.connected is False
    assert status.message == "Identifiants Google Contacts absents."


def test_ping_contacts_returns_disconnected_status() -> None:
    connector = Mock()
    connector.configured.return_value = True
    connector.list_contacts.side_effect = ContactsConnectorError(
        "Google Contacts n'est pas encore connecté."
    )

    with patch(
        "hanuman.services.core.contacts_service._connector",
        return_value=connector,
    ):
        status = ping_contacts()

    assert status.ok is False
    assert status.configured is True
    assert status.connected is False
    assert status.message == "Google Contacts n'est pas encore connecté."
