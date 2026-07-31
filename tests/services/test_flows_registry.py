from hanuman.models.registry import RegistryState
from hanuman.services.flows_registry import get_flows_registry


def test_flows_registry_is_explicitly_not_implemented() -> None:
    snapshot = get_flows_registry()

    assert snapshot.id == "flows"
    assert snapshot.label == "Flux"
    assert snapshot.state == RegistryState.NOT_IMPLEMENTED
    assert snapshot.implemented is False
    assert snapshot.entries == []
    assert snapshot.message is not None


def test_flows_registry_does_not_invent_entries() -> None:
    snapshot = get_flows_registry()

    assert len(snapshot.entries) == 0
