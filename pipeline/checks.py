"""Data quality checks on a fresh scrape, run before it is allowed into the history.

Formats and types (dates, times, age, access, availability) are enforced by Event itself,
so a bad value fails inside the extractor. These checks cover what a single Event can't know.
"""
from datetime import date

from pipeline.event import Event

REQUIRED = ("title", "venue", "url")
MAX_PAST_DAYS = 45     # venues list a few days of the current month; much older means a wrong year
MAX_AHEAD_DAYS = 400   # nobody announces gigs more than ~a year out
MIN_PREVIOUS = 4       # below this, a drop in the number of gigs is not meaningful
MAX_LISTED = 5


def check_events(source: str, events: list[Event], today: date, previous_upcoming: int) -> list[str]:
    """Return a list of problems; an empty list means the scrape is trustworthy."""
    problems = []

    for e in events:
        missing = [f for f in REQUIRED if not getattr(e, f)]
        if missing:
            problems.append(f"{source}: {e.title!r} is missing {', '.join(missing)}")
            continue
        day = date.fromisoformat(e.date)
        if (today - day).days > MAX_PAST_DAYS or (day - today).days > MAX_AHEAD_DAYS:
            problems.append(f"{source}: {e.title!r} is dated {e.date}, outside the expected range")
    if len(problems) > MAX_LISTED:
        problems = problems[:MAX_LISTED] + [f"{source}: ... and {len(problems) - MAX_LISTED} more"]

    upcoming = sum(1 for e in events if e.date >= today.isoformat())
    if previous_upcoming >= MIN_PREVIOUS and upcoming < previous_upcoming / 2:
        problems.append(f"{source}: only {upcoming} upcoming gigs, previously {previous_upcoming} "
                        "- the scraper probably broke")
    elif previous_upcoming > 0 and upcoming == 0:
        problems.append(f"{source}: no upcoming gigs, previously {previous_upcoming}")
    return problems
