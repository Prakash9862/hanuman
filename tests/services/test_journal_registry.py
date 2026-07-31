from hanuman.models.registry import RegistryState
from hanuman.services.journal_registry import get_journal_registry


def test_journal_registry_is_explicitly_not_implemented() -> None:
    snapshot = get_journal_registry()

    assert snapshot.id == "journal"
    assert snapshot.label == "Journal de Vie"
    assert snapshot.state == RegistryState.NOT_IMPLEMENTED
    assert snapshot.implemented is False
    assert snapshot.entries == []
    assert snapshot.message is not None


def test_journal_registry_does_not_invent_entries() -> None:
    snapshot = get_journal_registry()

    assert len(snapshot.entries) == 0
