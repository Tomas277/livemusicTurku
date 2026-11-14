"""The one shape every venue extractor produces.

Extractors build an Event, so a forgotten or misspelled field fails right where the mistake is.
The rest of the pipeline passes events around as plain dicts (Event.as_dict()), and load.py
derives its columns from this class, so a new field is added here and in the SQL only.
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
    age_limit: int | str | None = None
    access: str | None = None       # "tickets", "free", or None when the venue doesn't say
    availability: str | None = None  # "sold_out", "few", "available", or None

    def as_dict(self) -> dict:
        return asdict(self)


COLUMNS = tuple(f.name for f in fields(Event))
OPTIONAL = frozenset(f.name for f in fields(Event) if f.default is not MISSING)
