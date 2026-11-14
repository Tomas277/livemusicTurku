import re
from datetime import date
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from pipeline.access import classify
from pipeline.dates import infer_date
from pipeline.event import Event

SOURCE = "apollo"
VENUE = "Apollo"
BASE_URL = "https://apolloturku.fi/"
PAGES = {"keikat": BASE_URL + "keikat", "bilebandi": BASE_URL + "bilebandi"}


def parse(html: str, today: date, page_url: str = PAGES["keikat"]) -> list[Event]:
    """Parse one Apollo listing page. A party band playing "PE 13.11. - LA 14.11."
    becomes one event per night."""
    soup = BeautifulSoup(html, "lxml")
    events = []
    for ev in soup.select("div.bandevents__event"):
        title_el = ev.select_one(".bandevents__event--title")
        date_el = ev.select_one(".bandevents__event--date")
        if not (title_el and date_el):
            continue
        days = re.findall(r"([A-Za-zÄÖäö]{2})\s+(\d{1,2})\.(\d{1,2})\.", " ".join(date_el.get_text().split()))
        link = ev.select_one(".bandevents__event--cta a")
        buy = ev.select_one(".bandevents__event--cta a.buy")  # the ticket shop button
        access, availability = classify(buy.get_text(" ", strip=True) if buy else "", ticket_link=buy is not None)
        for weekday, day, month in days:
            events.append(Event(
                source=SOURCE,
                venue=VENUE,
                title=" ".join(title_el.get_text().split()),
                date=infer_date(int(day), int(month), today, weekday).isoformat(),
                access=access,
                availability=availability,
                url=urljoin(BASE_URL, link["href"]) if link and link.get("href") else page_url,
            ))
    return events


def extract(today: date) -> list[Event]:
    from pipeline.fetch import fetch_raw
    events = []
    for name, url in PAGES.items():
        events += parse(fetch_raw(SOURCE, url, today, name), today, url)
    return events
