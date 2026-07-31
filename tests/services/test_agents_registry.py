from hanuman.models.registry import RegistryState
from hanuman.services.agents_registry import get_agents_registry


def test_agents_registry_is_explicitly_not_implemented() -> None:
    snapshot = get_agents_registry()

    assert snapshot.id == "agents"
    assert snapshot.label == "Agents IA"
    assert snapshot.state == RegistryState.NOT_IMPLEMENTED
    assert snapshot.implemented is False
    assert snapshot.entries == []
    assert snapshot.message is not None


def test_agents_registry_does_not_invent_entries() -> None:
    snapshot = get_agents_registry()

    assert len(snapshot.entries) == 0
