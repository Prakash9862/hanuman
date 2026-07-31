from __future__ import annotations

from hanuman.models.registry import RegistrySnapshot, RegistryState


def get_flows_registry() -> RegistrySnapshot:
    return RegistrySnapshot(
        id="flows",
        label="Flux",
        state=RegistryState.NOT_IMPLEMENTED,
        implemented=False,
        entries=[],
        message="Aucun registre backend de flux n’est encore implémenté.",
    )
