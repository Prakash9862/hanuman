from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from hanuman.models.ping import PingResult
from hanuman.utils.decorators import trace_endpoint

DEFAULT_TIMEZONE = "Europe/Paris"

DayPeriod = Literal["night", "morning", "afternoon", "evening"]


@dataclass(frozen=True, slots=True)
class ClockSnapshot:
    """Représentation normalisée d'un instant dans Hanuman."""

    timezone: str
    local_datetime: str
    utc_datetime: str
    unix_timestamp: int
    date: str
    time: str
    weekday: int
    weekday_name: str
    iso_week: int
    period: DayPeriod

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


def _get_timezone(timezone_name: str) -> ZoneInfo:
    """Retourne un fuseau IANA valide."""

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Fuseau horaire inconnu : {timezone_name}") from exc


def _classify_period(value: datetime) -> DayPeriod:
    """Classe un instant selon la période locale de la journée."""

    hour = value.hour

    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 23:
        return "evening"

    return "night"


@trace_endpoint("clock", catch=True)
def ping_clock() -> PingResult:
    """Vérifie que la capacité temporelle locale est disponible."""

    now = datetime.now(UTC)

    return PingResult(
        ok=True,
        source="clock",
        detail={
            "provider": "python-stdlib",
            "utc_datetime": now.isoformat().replace("+00:00", "Z"),
            "default_timezone": DEFAULT_TIMEZONE,
        },
    )


def get_clock_snapshot(
    timezone_name: str = DEFAULT_TIMEZONE,
    *,
    at: datetime | None = None,
) -> ClockSnapshot:
    """Retourne un instant enrichi et normalisé dans le fuseau demandé.

    ``at`` est injectable afin de rendre les tests déterministes.
    Une date naïve est considérée comme exprimée en UTC.
    """

    timezone = _get_timezone(timezone_name)
    instant = at or datetime.now(UTC)

    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=UTC)

    utc_value = instant.astimezone(UTC)
    local_value = utc_value.astimezone(timezone)
    iso_calendar = local_value.isocalendar()

    return ClockSnapshot(
        timezone=timezone_name,
        local_datetime=local_value.isoformat(),
        utc_datetime=utc_value.isoformat().replace("+00:00", "Z"),
        unix_timestamp=int(utc_value.timestamp()),
        date=local_value.date().isoformat(),
        time=local_value.time().replace(microsecond=0).isoformat(),
        weekday=iso_calendar.weekday,
        weekday_name=local_value.strftime("%A"),
        iso_week=iso_calendar.week,
        period=_classify_period(local_value),
    )


def normalize_datetime(
    value: datetime,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> datetime:
    """Normalise un instant vers le fuseau demandé.

    Une date naïve est interprétée comme UTC pour éviter toute dépendance
    implicite au fuseau de la machine.
    """

    timezone = _get_timezone(timezone_name)

    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)

    return value.astimezone(timezone)


def measure_duration_ms(
    started_at: datetime,
    ended_at: datetime | None = None,
) -> int:
    """Calcule une durée positive en millisecondes."""

    start = started_at
    end = ended_at or datetime.now(UTC)

    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)

    duration_ms = int((end.astimezone(UTC) - start.astimezone(UTC)).total_seconds() * 1000)

    if duration_ms < 0:
        raise ValueError("ended_at doit être postérieur ou égal à started_at")

    return duration_ms


def list_timezones(query: str | None = None, limit: int = 100) -> list[str]:
    """Liste les fuseaux IANA, avec filtre facultatif et limite bornée."""

    if limit < 1 or limit > 500:
        raise ValueError("limit doit être compris entre 1 et 500")

    timezones = sorted(available_timezones())

    if query:
        normalized_query = query.casefold().strip()
        timezones = [
            timezone_name
            for timezone_name in timezones
            if normalized_query in timezone_name.casefold()
        ]

    return timezones[:limit]
