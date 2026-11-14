"""The one shape every venue extractor produces.

Extractors build an Event with make_event/add_event, so a forgotten or misspelled field fails right
where the mistake is, and a gig with a bad value is skipped and logged instead of rejecting the source. The whole pipeline passes Events around; load.py turns them
into rows. A new field is added in three places: the Event class, SQL_TYPES below, and the
SELECT lists in pipeline/transform/*.sql.
"""
import datetime
import re
import sys
from dataclasses import dataclass, fields

ACCESS = (None, "tickets", "free")
AVAILABILITY = (None, "sold_out", "few", "available")
_TIME = re.compile(r"([01]\d|2[0-3]):[0-5]\d")


@dataclass(frozen=True)
class Event:
    source: str
    venue: str
    title: str
    date: str                       # ISO date, e.g. "2026-11-14"
    url: str
    doors: str | None = None        # "HH:MM"
    start: str | None = None        # "HH:MM"
    age_limit: int | None = None
    access: str | None = None       # "tickets", "free", or None when the venue doesn't say
    availability: str | None = None  # "sold_out", "few", "available", or None

    def __post_init__(self) -> None:
        """Reject a gig that is unusable. make_event() turns the error into a skipped gig."""
        for name in ("title", "venue", "url"):
            value = getattr(self, name)
            if not (isinstance(value, str) and value.strip()):
                raise ValueError(f"{name} is empty")
        try:
            datetime.date.fromisoformat(self.date)
        except (TypeError, ValueError):
            raise ValueError(f"date {self.date!r} is not YYYY-MM-DD") from None
        for name in ("doors", "start"):
            value = getattr(self, name)
            if value is not None and not (isinstance(value, str) and _TIME.fullmatch(value)):
                raise ValueError(f"{name} {value!r} is not HH:MM")
        if self.age_limit is not None and (not isinstance(self.age_limit, int) or isinstance(self.age_limit, bool)):
            raise ValueError(f"age_limit {self.age_limit!r} is not a number")
        if self.access not in ACCESS:
            raise ValueError(f"unknown access {self.access!r}")
        if self.availability not in AVAILABILITY:
            raise ValueError(f"unknown availability {self.availability!r}")


def make_event(**fields) -> Event | None:
    """Build an Event, or log why the gig is skipped and return None. One malformed gig on a
    venue's site must not cost the whole source; checks.check_events still guards against a mass failure."""
    try:
        return Event(**fields)
    except ValueError as exc:
        what = fields.get("title") or fields.get("url")
        print(f"{fields.get('source')}: skipped {what!r} - {exc}", file=sys.stderr)
        return None


def add_event(events: list[Event], **fields) -> None:
    """Append make_event(**fields) to events unless the gig was skipped."""
    event = make_event(**fields)
    if event:
        events.append(event)


COLUMNS = tuple(f.name for f in fields(Event))


# DuckDB type of every Event field, in the order the history CSV stores them. The staging and
# history tables are generated from this, so the types are defined once.
SQL_TYPES = {
    "source": "VARCHAR", "venue": "VARCHAR", "title": "VARCHAR", "date": "DATE",
    "doors": "VARCHAR", "start": "VARCHAR", "age_limit": "INTEGER", "url": "VARCHAR",
    "access": "VARCHAR", "availability": "VARCHAR",
}
HISTORY_TYPES = {**SQL_TYPES, "first_seen": "DATE", "last_seen": "DATE"}
