"""The one shape every venue extractor produces.

Extractors build an Event, so a forgotten or misspelled field, or a value in the wrong format,
fails right where the mistake is. The whole pipeline passes Events around; load.py turns them
into rows. A new field is added in three places: the Event class, SQL_TYPES below, and the
SELECT lists in pipeline/transform/*.sql.
"""
import datetime
import re
from dataclasses import dataclass, fields

ACCESS = (None, "tickets", "free")
AVAILABILITY = (None, "sold_out", "few", "available")
_TIME = re.compile(r"\d{2}:\d{2}")


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
        label = f"{self.source}: {self.title!r}"
        try:
            datetime.date.fromisoformat(self.date)
        except (TypeError, ValueError):
            raise ValueError(f"{label} has date {self.date!r}, expected YYYY-MM-DD") from None
        for name in ("doors", "start"):
            value = getattr(self, name)
            if value is not None and not (isinstance(value, str) and _TIME.fullmatch(value)):
                raise ValueError(f"{label} has {name} {value!r}, expected HH:MM")
        if self.age_limit is not None and (not isinstance(self.age_limit, int) or isinstance(self.age_limit, bool)):
            raise ValueError(f"{label} has age_limit {self.age_limit!r}, expected a number")
        if self.access not in ACCESS:
            raise ValueError(f"{label} has unknown access {self.access!r}")
        if self.availability not in AVAILABILITY:
            raise ValueError(f"{label} has unknown availability {self.availability!r}")


COLUMNS = tuple(f.name for f in fields(Event))


# DuckDB type of every Event field, in the order the history CSV stores them. The staging and
# history tables are generated from this, so the types are defined once.
SQL_TYPES = {
    "source": "VARCHAR", "venue": "VARCHAR", "title": "VARCHAR", "date": "DATE",
    "doors": "VARCHAR", "start": "VARCHAR", "age_limit": "INTEGER", "url": "VARCHAR",
    "access": "VARCHAR", "availability": "VARCHAR",
}
HISTORY_TYPES = {**SQL_TYPES, "first_seen": "DATE", "last_seen": "DATE"}
