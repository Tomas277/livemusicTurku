import re
import time
from datetime import date

import httpx
from bs4 import BeautifulSoup

from pipeline.access import classify
from pipeline.dates import find_time
from pipeline.event import Event

SOURCE = "logomo"
VENUE = "Logomo"
SITEMAP_URL = "https://logomo.fi/logomo_event-sitemap.xml"


def event_urls(sitemap_xml: str) -> list[str]:
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap_xml)
    return [u for u in urls if "/tapahtuma/" in u]  # skips the archive page itself


def parse_event(html: str, url: str, today: date) -> dict | None:
    """One Logomo event page -> event dict, or None for pages with no date or past events."""
    soup = BeautifulSoup(html, "lxml")
    title_el = soup.select_one("h1")
    meta_el = soup.select_one(".logomo-event__meta")
    if not (title_el and meta_el):
        return None
    meta = " ".join(meta_el.get_text(" ").split())
    m = re.search(r"Päivä:\s*(\d{1,2})\.(\d{1,2})\.(\d{4})", meta)
    if not m:
        return None
    day = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    if day < today:  # the sitemap still lists events back to 2022
        return None
    age = re.search(r"Ikäraja:\s*(\S+)", meta)
    title = " ".join(title_el.get_text(" ").split())
    shop = meta_el.select_one("a[href*='livex'], a[href*='lippu.fi'], a[href*='ticketmaster']")
    access, availability = classify(f"{title} {meta}", ticket_link=shop is not None)
    # "*LOPPUUNMYYTY*" is part of the title on their site; keep it out of the name so the gig keeps one identity.
    title = re.sub(r"\s*[/*–-]*\s*\*?loppuunmyyty\*?\s*[/*]*", "", title, flags=re.I).strip(" /–-")
    return Event(
        source=SOURCE,
        venue=VENUE,
        title=title,
        date=day.isoformat(),
        start=find_time(r"Tapahtuma alkaa:", meta),
        age_limit=age.group(1) if age else None,
        access=access,
        availability=availability,
        url=url,
    ).as_dict()


def extract(today: date) -> list[dict]:
    from pipeline.fetch import HEADERS, fetch_raw
    sitemap = httpx.get(SITEMAP_URL, headers=HEADERS, follow_redirects=True, timeout=30)
    sitemap.raise_for_status()
    events = []
    # Logomo's event list is an Ajax Load More widget that can't be queried reliably,
    # so read every event page from the sitemap (one polite request at a time).
    for url in event_urls(sitemap.text):
        name = url.rstrip("/").rsplit("/", 1)[-1]
        event = parse_event(fetch_raw(SOURCE, url, today, name), url, today)
        if event:
            events.append(event)
        time.sleep(0.3)
    return events
