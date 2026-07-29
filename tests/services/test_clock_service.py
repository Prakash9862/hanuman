from datetime import UTC, datetime

import pytest

from hanuman.services.core.clock_service import (
    get_clock_snapshot,
    list_timezones,
    measure_duration_ms,
    normalize_datetime,
    ping_clock,
)


def test_ping_clock_returns_success() -> None:
    result = ping_clock()

    assert result.ok is True
    assert result.source == "clock"
    assert result.detail["provider"] == "python-stdlib"
    assert result.detail["default_timezone"] == "Europe/Paris"


def test_get_clock_snapshot_for_paris_in_summer() -> None:
    instant = datetime(2026, 7, 29, 20, 43, tzinfo=UTC)

    snapshot = get_clock_snapshot("Europe/Paris", at=instant)

    assert snapshot.timezone == "Europe/Paris"
    assert snapshot.local_datetime == "2026-07-29T22:43:00+02:00"
    assert snapshot.utc_datetime == "2026-07-29T20:43:00Z"
    assert snapshot.date == "2026-07-29"
    assert snapshot.time == "22:43:00"
    assert snapshot.weekday == 3
    assert snapshot.iso_week == 31
    assert snapshot.period == "evening"


@pytest.mark.parametrize(
    ("hour", "expected_period"),
    [
        (2, "night"),
        (7, "morning"),
        (14, "afternoon"),
        (21, "evening"),
        (23, "night"),
    ],
)
def test_get_clock_snapshot_classifies_day_period(
    hour: int,
    expected_period: str,
) -> None:
    instant = datetime(2026, 1, 15, hour, 0, tzinfo=UTC)

    snapshot = get_clock_snapshot("UTC", at=instant)

    assert snapshot.period == expected_period


def test_normalize_datetime_converts_to_requested_timezone() -> None:
    instant = datetime(2026, 7, 29, 20, 43, tzinfo=UTC)

    normalized = normalize_datetime(instant, "Europe/Paris")

    assert normalized.isoformat() == "2026-07-29T22:43:00+02:00"


def test_normalize_datetime_treats_naive_datetime_as_utc() -> None:
    instant = datetime(2026, 7, 29, 20, 43)

    normalized = normalize_datetime(instant, "Europe/Paris")

    assert normalized.isoformat() == "2026-07-29T22:43:00+02:00"


def test_measure_duration_ms() -> None:
    started_at = datetime(2026, 7, 29, 20, 0, tzinfo=UTC)
    ended_at = datetime(2026, 7, 29, 20, 0, 3, 500000, tzinfo=UTC)

    assert measure_duration_ms(started_at, ended_at) == 3500


def test_measure_duration_ms_rejects_negative_duration() -> None:
    started_at = datetime(2026, 7, 29, 20, 1, tzinfo=UTC)
    ended_at = datetime(2026, 7, 29, 20, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="ended_at"):
        measure_duration_ms(started_at, ended_at)


def test_list_timezones_filters_results() -> None:
    results = list_timezones(query="Paris", limit=10)

    assert "Europe/Paris" in results


def test_list_timezones_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError, match="limit"):
        list_timezones(limit=0)


def test_get_clock_snapshot_rejects_unknown_timezone() -> None:
    with pytest.raises(ValueError, match="Fuseau horaire inconnu"):
        get_clock_snapshot("Mars/Olympus_Mons")
