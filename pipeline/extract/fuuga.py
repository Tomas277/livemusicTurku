import html
import re
from datetime import date

import httpx

from pipeline.dates import infer_date
from pipeline.event import Event

SOURCE = "fuuga"
VENUE = "Fuuga"
API_URL = "https://www.musiikkitalofuuga.fi/wp-json/karhu-content-filtered-search/v1/get-content"
MAX_PAGES = 40
MONTHS = {
    "tammikuuta": 1, "helmikuuta": 2, "maaliskuuta": 3, "huhtikuuta": 4, "toukokuuta": 5, "kesäkuuta": 6,
    "heinäkuuta": 7, "elokuuta": 8, "syyskuuta": 9, "lokakuuta": 10, "marraskuuta": 11, "joulukuuta": 12,
}
# Fuuga also hosts talk shows and ballet; a gig with only these genres is not music.
NON_MUSIC_GENRES = {"talkshow", "tanssi"}
# Rooms inside the house are all just "Fuuga" (same choice as Fuusio); other places keep their name.
FUUGA_ROOMS = {"konserttisali", "ateljee", "viinibaari fino"}


def _text(value: str) -> str:
    return " ".join(html.unescape(value).split())


def parse(data: dict, today: date) -> list[Event]:
    """Turn one page of the site's search API response into event dicts."""
    events = []
    for item in data.get("contentList") or []:
        d = item.get("data", {})
        month = MONTHS.get(str(d.get("eventDateMonth", "")).lower())
        if not (month and str(d.get("eventDateDayNum", "")).isdigit() and d.get("title") and d.get("url")):
            continue
        genres = {_text(g).lower() for g in d.get("eventGen") or []}
        if genres and genres <= NON_MUSIC_GENRES:
            continue
        # "date" in the response is the first night of a run, so the real night comes from the day/month fields.
        day = infer_date(int(d["eventDateDayNum"]), month, today, str(d.get("eventDateDay", "")).lower() or None)
        room = _text((d.get("eventVenue") or [""])[0])
        start = re.match(r"\d{1,2}:\d{2}", d.get("eventTime") or "")
        # The site colours each concert's ticket status; it is the only venue that tells us how many are left.
        status = str(d.get("capacityStatus") or "").lower()
        availability = {"red": "sold_out", "yellow": "few", "green": "available"}.get(status)
        has_tickets = availability is not None or bool(d.get("buyLink") or d.get("showBuyLink"))
        events.append(Event(
            source=SOURCE,
            venue=VENUE if room.lower() in FUUGA_ROOMS or not room else room,
            title=_text(d["title"]),
            date=day.isoformat(),
            start=f"{int(start.group().split(':')[0]):02d}:{start.group().split(':')[1]}" if start else None,
            access="tickets" if has_tickets else None,
            availability=availability,
            url=d["url"],
        ))
    return events


def _match_key(e: Event) -> tuple:
    # The orchestra lists the same concert without the "TFO: " style prefix the house uses.
    title = re.sub(r"^[A-ZÅÄÖ0-9]{2,6}:\s*", "", e.title).lower()
    return e.venue, e.date, e.start, title


def dedupe(events: list[Event]) -> list[Event]:
    """One event per concert; of two twins keep the one with the longer (more informative) title."""
    best: dict[tuple, Event] = {}
    for e in events:
        k = _match_key(e)
        if k not in best or len(e.title) > len(best[k].title):
            best[k] = e
    return list(best.values())


def extract(today: date) -> list[Event]:
    from pipeline.fetch import HEADERS, save_raw
    events = []
    for page in range(1, MAX_PAGES + 1):
        body = {"page": page, "search_key": "", "filters": {}, "post_types": "event", "show_only_terms": "",
                "dynamic_filters": "", "filter_options": "", "lang": "fi", "meta": {}}
        resp = httpx.post(API_URL, json=body, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        save_raw(SOURCE, today, f"page{page}", resp.text)
        data = resp.json()
        if not data.get("contentList"):  # past the last page the list is simply empty
            break
        events.extend(parse(data, today))
    return dedupe(events)
