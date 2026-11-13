import re
from datetime import date

from bs4 import BeautifulSoup

SOURCE = "fuuga"
VENUE = "Fuuga"
LIST_URL = "https://tfo.fi/tapahtumat/"
MAX_PAGES = 20
# "Musiikkitalo Fuuga, Konserttisali" -> "Fuuga" (no room names, same as Fuusio)
_SOLD_OUT = re.compile(r"^(?:loppuunmyyty|sold out):\s*", re.I)


def _venue(location: str) -> str | None:
    """Venue name for a concert, or None when it is played outside Turku."""
    if "fuuga" in location.lower():
        return VENUE
    if "helsingin" in location.lower():  # the orchestra tours, e.g. a Helsinki Music Centre guest concert
        return None
    return location or VENUE


def parse(html: str, today: date) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    events = []
    for art in soup.select("article.tapahtuma-lift-item"):
        link = art.select_one("h3 a")
        when = art.select_one(".tapahtuma-lift-meta")
        if not (link and when):
            continue
        m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4}),\s*(\d{1,2}):(\d{2})", " ".join(when.get_text(" ").split()))
        if not m:
            continue
        location = art.select_one(".tapahtuma-lift-location")
        venue = _venue(" ".join(location.get_text(" ").split())) if location else VENUE
        if venue is None:
            continue
        events.append({
            "source": SOURCE,
            "venue": venue,
            "title": _SOLD_OUT.sub("", " ".join(link.get_text(" ").split())),
            "date": date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat(),
            "doors": None,
            "start": f"{int(m.group(4)):02d}:{m.group(5)}",
            "age_limit": None,
            "url": link["href"],
        })
    return events


def extract(today: date) -> list[dict]:
    from pipeline.fetch import fetch_raw
    events, seen = [], set()
    for page in range(1, MAX_PAGES + 1):
        url = LIST_URL if page == 1 else f"{LIST_URL}?page={page}"
        batch = parse(fetch_raw(SOURCE, url, today, f"page{page}"), today)
        fresh = [e for e in batch if (e["url"], e["date"]) not in seen]
        if not fresh:  # past the last page the site just returns an empty list
            break
        seen.update((e["url"], e["date"]) for e in fresh)
        events.extend(fresh)
    return events
