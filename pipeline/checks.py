"""Data quality checks on a fresh scrape, run before it is allowed into the history."""
import re
from datetime import date

REQUIRED = ("title", "date", "venue", "url")
MAX_PAST_DAYS = 45     # venues list a few days of the current month; much older means a wrong year
MAX_AHEAD_DAYS = 400   # nobody announces gigs more than ~a year out
MIN_PREVIOUS = 4       # below this, a drop in the number of gigs is not meaningful
MAX_LISTED = 5
TIME = re.compile(r"\d{2}:\d{2}")
ACCESS = {None, "tickets", "free"}
AVAILABILITY = {None, "sold_out", "few", "available"}


def _format_problems(source: str, e: dict) -> list[str]:
    """Wrong types or formats would otherwise only blow up later, inside the database load."""
    found = []
    age = e.get("age_limit")
    if age is not None and (not isinstance(age, int) or isinstance(age, bool)):
        found.append(f"{source}: {e['title']!r} has age_limit {age!r}, expected a number")
    for field in ("doors", "start"):
        value = e.get(field)
        if value is not None and not (isinstance(value, str) and TIME.fullmatch(value)):
            found.append(f"{source}: {e['title']!r} has {field} {value!r}, expected HH:MM")
    if e.get("access") not in ACCESS:
        found.append(f"{source}: {e['title']!r} has unknown access {e.get('access')!r}")
    if e.get("availability") not in AVAILABILITY:
        found.append(f"{source}: {e['title']!r} has unknown availability {e.get('availability')!r}")
    return found


def check_events(source: str, events: list[dict], today: date, previous_upcoming: int) -> list[str]:
    """Return a list of problems; an empty list means the scrape is trustworthy."""
    problems = []

    for e in events:
        missing = [f for f in REQUIRED if not e.get(f)]
        if missing:
            problems.append(f"{source}: {e.get('title')!r} is missing {', '.join(missing)}")
            continue
        try:
            day = date.fromisoformat(e["date"])
        except ValueError:
            problems.append(f"{source}: {e['title']!r} has an invalid date {e['date']!r}")
            continue
        if (today - day).days > MAX_PAST_DAYS or (day - today).days > MAX_AHEAD_DAYS:
            problems.append(f"{source}: {e['title']!r} is dated {e['date']}, outside the expected range")
        problems += _format_problems(source, e)
    if len(problems) > MAX_LISTED:
        problems = problems[:MAX_LISTED] + [f"{source}: ... and {len(problems) - MAX_LISTED} more"]

    upcoming = sum(1 for e in events if e.get("date", "") >= today.isoformat())
    if previous_upcoming >= MIN_PREVIOUS and upcoming < previous_upcoming / 2:
        problems.append(f"{source}: only {upcoming} upcoming gigs, previously {previous_upcoming} "
                        "- the scraper probably broke")
    elif previous_upcoming > 0 and upcoming == 0:
        problems.append(f"{source}: no upcoming gigs, previously {previous_upcoming}")
    return problems
