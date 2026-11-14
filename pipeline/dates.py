import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

FI_WEEKDAYS = {
    "maanantai": 0, "tiistai": 1, "keskiviikko": 2, "torstai": 3,
    "perjantai": 4, "lauantai": 5, "sunnuntai": 6,
    "ma": 0, "ti": 1, "ke": 2, "to": 3, "pe": 4, "la": 5, "su": 6,
}

TURKU = ZoneInfo("Europe/Helsinki")
_TIME = r"(\d{1,2})(?:[:.](\d{2}))?"


def today_in_turku(now: datetime | None = None) -> date:
    """Today's date in Turku. The CI runner's clock is UTC, which is 2-3 hours behind and would
    give yesterday's date late in the evening."""
    return (now or datetime.now(TURKU)).astimezone(TURKU).date()


def find_time(prefix: str, text: str) -> str | None:
    """Find a clock time after a keyword pattern, e.g. find_time('ovet\\s*klo', ...) -> '20:30'."""
    m = re.search(prefix + r"\s*" + _TIME, text, re.IGNORECASE)
    if not m:
        return None
    return f"{int(m.group(1)):02d}:{m.group(2) or '00'}"


def normalize_time(text: str) -> str | None:
    """'9:30' or '19:00 - 21:00' -> the first clock time as 'HH:MM'; None when there is none."""
    m = re.match(r"\s*(\d{1,2}):(\d{2})", text)
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def infer_date(day: int, month: int, today: date, weekday: str | None = None) -> date:
    """Resolve a day+month with no year to a full date.

    Venues list events up to ~a year ahead and still show yesterday's night,
    so the right year is the candidate closest to today. If the page shows a
    weekday name, only candidates with that weekday are considered.
    """
    candidates = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidates.append(date(year, month, day))
        except ValueError:  # e.g. 29.2. in a non-leap year
            continue
    wd = FI_WEEKDAYS.get(weekday.strip().lower().rstrip(".")) if weekday else None
    matching = [c for c in candidates if wd is None or c.weekday() == wd]
    pool = matching or candidates
    return min(pool, key=lambda c: abs((c - today).days))
