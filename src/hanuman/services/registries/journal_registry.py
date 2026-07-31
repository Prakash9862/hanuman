from __future__ import annotations

from hanuman.models.registry import RegistrySnapshot, RegistryState


def get_journal_registry() -> RegistrySnapshot:
    return RegistrySnapshot(
        id="journal",
        label="Journal de Vie",
        state=RegistryState.NOT_IMPLEMENTED,
        implemented=False,
        entries=[],
        message="Le Journal de Vie ne possède pas encore de registre backend.",
    )
