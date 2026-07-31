from __future__ import annotations

from hanuman.models.registry import RegistrySnapshot, RegistryState


def get_agents_registry() -> RegistrySnapshot:
    return RegistrySnapshot(
        id="agents",
        label="Agents IA",
        state=RegistryState.NOT_IMPLEMENTED,
        implemented=False,
        entries=[],
        message="Aucun agent backend n’est encore enregistré.",
    )
