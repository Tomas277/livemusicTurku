"""The one shape every venue extractor produces.

Extractors build an Event, so a forgotten or misspelled field fails right where the mistake is.
The rest of the pipeline passes events around as plain dicts (Event.as_dict()), and load.py
derives its columns from this class. A new field is added in three places: the Event class,
SQL_TYPES below, and the SELECT lists in pipeline/transform/*.sql.
"""
from dataclasses import MISSING, asdict, dataclass, fields


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

    def as_dict(self) -> dict:
        return asdict(self)


COLUMNS = tuple(f.name for f in fields(Event))
OPTIONAL = frozenset(f.name for f in fields(Event) if f.default is not MISSING)


# DuckDB type of every Event field, in the order the history CSV stores them. The staging and
# history tables are generated from this, so the types are defined once.
SQL_TYPES = {
    "source": "VARCHAR", "venue": "VARCHAR", "title": "VARCHAR", "date": "DATE",
    "doors": "VARCHAR", "start": "VARCHAR", "age_limit": "INTEGER", "url": "VARCHAR",
    "access": "VARCHAR", "availability": "VARCHAR",
}
HISTORY_TYPES = {**SQL_TYPES, "first_seen": "DATE", "last_seen": "DATE"}
