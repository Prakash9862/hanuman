from __future__ import annotations

from typing import Any

import pytest

from hanuman.api.core import calendar


def test_calendar_status_list_events_and_ping_delegate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calendars = [{"id": "one"}, {"id": "two"}]
    events = [{"id": "event"}]
    monkeypatch.setattr(calendar, "get_calendars", lambda: calendars)
    monkeypatch.setattr(calendar, "get_upcoming_events", lambda max_results: events)
    request: Any = None

    assert calendar.calendar_status(request) == {
        "ok": True,
        "connected": True,
        "calendar_count": 2,
    }
    assert calendar.calendar_list(request) == {
        "ok": True,
        "count": 2,
        "calendars": calendars,
    }
    assert calendar.calendar_events(request, 5) == {
        "ok": True,
        "count": 1,
        "events": events,
    }
    ping = calendar.calendar_ping(request)
    assert ping["source"] == "calendar"
    assert ping["detail"] == {"calendar_count": 2}
    assert ping["timestamp"].endswith("+00:00")
