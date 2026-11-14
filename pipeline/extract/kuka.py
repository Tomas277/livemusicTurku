import re
from datetime import date

from bs4 import BeautifulSoup

from pipeline.access import classify
from pipeline.dates import find_time, infer_date
from pipeline.event import Event

SOURCE = "kuka"
VENUE = "Kuka"
PROGRAM_URL = "https://barkuka.fi/ohjelma/"


def _clean(text: str) -> str:
    return " ".join(text.replace("­", "").split())


def parse(html: str, today: date) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    events = []
    for ev in soup.select("div.event"):
        date_el = ev.select_one("p.eventdate")
        title_el = ev.select_one("h3.eventtitle")
        if not (date_el and title_el):
            continue
        m = re.search(r"([a-zäö]{2})\s+(\d{1,2})\.(\d{1,2})\.", _clean(date_el.get_text()), re.I)
        if not m:
            continue
        excerpt = ev.select_one("p.eventexcerpt")
        link = ev.select_one("a.newsreadmore")
        access, availability = classify(_clean(f"{title_el.get_text()} {excerpt.get_text() if excerpt else ''}"))
        events.append(Event(
            source=SOURCE,
            venue=VENUE,
            title=_clean(title_el.get_text("")),
            date=infer_date(int(m.group(2)), int(m.group(3)), today, m.group(1)).isoformat(),
            start=find_time(r"(?:klo|alkaen)", _clean(excerpt.get_text())) if excerpt else None,
            access=access,
            availability=availability,
            url=link["href"] if link else PROGRAM_URL,
        ).as_dict())
    return events


def extract(today: date) -> list[dict]:
    from pipeline.fetch import fetch_raw
    return parse(fetch_raw(SOURCE, PROGRAM_URL, today), today)
