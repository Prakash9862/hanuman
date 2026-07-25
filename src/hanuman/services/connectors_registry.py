from __future__ import annotations

from hanuman.models.connectors import (
    CapabilityProvider,
    ConnectorDescriptor,
    ConnectorKind,
)

_CONNECTORS: tuple[ConnectorDescriptor, ...] = (
    ConnectorDescriptor(
        id="gmail",
        label="Gmail",
        description="Lecture et recherche des messages Gmail.",
        kind=ConnectorKind.REMOTE_API,
        capabilities=[
            "mail.read",
            "mail.search",
            "mail.read_important",
        ],
        requires_auth=True,
        status_endpoint="/gmail/status",
    ),
    ConnectorDescriptor(
        id="calendar",
        label="Google Calendar",
        description="Lecture des calendriers, événements à venir et liens Google Maps.",
        kind=ConnectorKind.REMOTE_API,
        capabilities=[
            "calendar.read",
            "calendar.list_calendars",
            "calendar.list_events",
            "maps.open_location",
            "maps.open_directions",
        ],
        requires_auth=True,
        status_endpoint="/calendar/status",
    ),
    ConnectorDescriptor(
        id="github",
        label="GitHub",
        description="Accès aux dépôts, issues et activités GitHub.",
        kind=ConnectorKind.REMOTE_API,
        capabilities=[
            "code.read_repositories",
            "code.read_issues",
            "code.read_activity",
        ],
        requires_auth=True,
        status_endpoint="/github/ping",
    ),
    ConnectorDescriptor(
        id="notion",
        label="Notion",
        description="Lecture, recherche et publication de pages Notion.",
        kind=ConnectorKind.REMOTE_API,
        capabilities=[
            "knowledge.read",
            "knowledge.search",
            "knowledge.write",
        ],
        writable=True,
        requires_auth=True,
        status_endpoint="/notion/ping",
    ),
    ConnectorDescriptor(
        id="obsidian",
        label="Obsidian",
        description="Lecture et écriture de notes dans le vault local.",
        kind=ConnectorKind.LOCAL_FILESYSTEM,
        capabilities=[
            "notes.read",
            "notes.search",
            "notes.write",
            "notes.list",
        ],
        writable=True,
        status_endpoint="/obsidian/ping",
    ),
    ConnectorDescriptor(
        id="openai",
        label="OpenAI",
        description="Analyse, résumé et génération de texte structurée.",
        kind=ConnectorKind.AI_PROVIDER,
        capabilities=[
            "ai.summarize",
            "ai.classify",
            "ai.extract",
            "ai.generate",
        ],
        requires_auth=True,
        status_endpoint="/openai/ping",
    ),
    ConnectorDescriptor(
        id="wikipedia",
        label="Wikipédia",
        description="Recherche et extraction de contenu encyclopédique.",
        kind=ConnectorKind.REMOTE_API,
        capabilities=[
            "encyclopedia.search",
            "encyclopedia.read",
        ],
        status_endpoint="/wikipedia/ping",
    ),
    ConnectorDescriptor(
        id="chess-com",
        label="Chess.com",
        description="Récupération des parties et données publiques Chess.com.",
        kind=ConnectorKind.REMOTE_API,
        capabilities=[
            "chess.read_games",
            "chess.read_player",
            "chess.export_pgn",
        ],
        status_endpoint="/chess/ping",
    ),
    ConnectorDescriptor(
        id="youtube",
        label="YouTube",
        description="Recherche de vidéos, chaînes et playlists via YouTube Data API.",
        kind=ConnectorKind.REMOTE_API,
        capabilities=[
            "video.search",
            "video.read_metadata",
            "video.open",
        ],
        requires_auth=True,
        status_endpoint="/resources/youtube/status",
    ),
    ConnectorDescriptor(
        id="gallica",
        label="Gallica",
        description="Recherche de documents numérisés dans les collections de la BnF.",
        kind=ConnectorKind.REMOTE_API,
        capabilities=[
            "heritage.search",
            "heritage.read_metadata",
            "heritage.open_document",
        ],
        status_endpoint="/resources/gallica/status",
    ),
    ConnectorDescriptor(
        id="imslp",
        label="IMSLP",
        description="Recherche et ouverture de partitions dans la bibliothèque IMSLP.",
        kind=ConnectorKind.REMOTE_API,
        capabilities=[
            "music_score.search",
            "music_score.open_search",
        ],
        status_endpoint="/resources/imslp/status",
    ),
)


def list_connectors() -> list[ConnectorDescriptor]:
    return [connector.model_copy(deep=True) for connector in _CONNECTORS]


def get_connector(connector_id: str) -> ConnectorDescriptor | None:
    normalized = connector_id.strip().lower()
    for connector in _CONNECTORS:
        if connector.id == normalized:
            return connector.model_copy(deep=True)
    return None


def list_capabilities() -> list[CapabilityProvider]:
    providers: dict[str, list[str]] = {}
    for connector in _CONNECTORS:
        for capability in connector.capabilities:
            providers.setdefault(capability, []).append(connector.id)

    return [
        CapabilityProvider(capability=capability, connector_ids=sorted(connector_ids))
        for capability, connector_ids in sorted(providers.items())
    ]


def providers_for(capability: str) -> list[ConnectorDescriptor]:
    normalized = capability.strip().lower()
    return [
        connector.model_copy(deep=True)
        for connector in _CONNECTORS
        if normalized in connector.capabilities
    ]
