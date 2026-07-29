from __future__ import annotations

from hanuman.services.connectors_registry import (
    get_connector,
    list_capabilities,
    list_connectors,
    providers_for,
)


def test_registry_contains_existing_connectors() -> None:
    connector_ids = {connector.id for connector in list_connectors()}

    assert connector_ids == {
        "anki",
        "gmail",
        "calendar",
        "github",
        "notion",
        "obsidian",
        "openai",
        "wikipedia",
        "chess-com",
        "youtube",
        "gallica",
        "imslp",
    }


def test_get_connector_returns_copy() -> None:
    first = get_connector("calendar")
    second = get_connector("calendar")

    assert first is not None
    assert second is not None
    assert first == second
    assert first is not second


def test_unknown_connector_returns_none() -> None:
    assert get_connector("unknown") is None


def test_capabilities_are_sorted_and_have_providers() -> None:
    capabilities = list_capabilities()
    names = [item.capability for item in capabilities]

    assert names == sorted(names)
    assert all(item.connector_ids for item in capabilities)


def test_provider_lookup() -> None:
    providers = providers_for("knowledge.write")

    assert [provider.id for provider in providers] == ["notion"]
    assert providers_for("missing.capability") == []


def test_calendar_exposes_maps_capabilities() -> None:
    calendar = get_connector("calendar")

    assert calendar is not None
    assert "maps.open_location" in calendar.capabilities
    assert "maps.open_directions" in calendar.capabilities
