import json
import re
from datetime import date

from bs4 import BeautifulSoup

from pipeline.event import Event
from pipeline.fetch import fetch_raw, post, save_raw

SOURCE = "fuusio"
VENUE = "Fuusio"
PROGRAM_URL = "https://fuusioturku.fi/ohjelma/"
AJAX_ACTION = "sugar_calendar_event_list_block_update"
MAX_PAGES = 10

# Fuusio puts the room in the title ("Band /Nirvana"). The site shows one venue, so drop it.
_ROOMS = r"(?:nirvana|livesali|live|level2|ug klubi|ug|utopia)"
_STAGE_SUFFIX = re.compile(r"\s*/\s*" + _ROOMS + r"\s*$", re.IGNORECASE)
_STAGE_PREFIX = re.compile(r"^" + _ROOMS + r":\s*", re.IGNORECASE)


def _clean_title(title: str) -> str:
    return _STAGE_PREFIX.sub("", _STAGE_SUFFIX.sub("", " ".join(title.split())))


def parse(html: str) -> list[Event]:
    """Parse a full program page or the HTML fragment the 'Next' button loads."""
    soup = BeautifulSoup(html, "lxml")
    events = []
    for ev in soup.select(".sugar-calendar-event-list-block__gridview__event"):
        link = ev.select_one("h4 a")
        when = ev.select_one("time[datetime]")
        if not (link and when):
            continue
        events.append(Event(
            source=SOURCE,
            venue=VENUE,
            title=_clean_title(link.get_text()),
            date=when["datetime"][:10],
            url=link["href"],
        ))
    return events


def next_enabled(html: str) -> bool:
    btn = BeautifulSoup(html, "lxml").select_one(".sugar-calendar-event-list-block__footer__next_btn")
    return btn is not None and not btn.has_attr("disabled")


def _flatten(prefix: str, value, out: dict) -> None:
    """Encode nested data the way jQuery does for form posts: a[b][]=..."""
    if isinstance(value, dict):
        for k, v in value.items():
            _flatten(f"{prefix}[{k}]", v, out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _flatten(f"{prefix}[{i}]" if isinstance(v, (dict, list)) else f"{prefix}[]", v, out)
    else:
        out[prefix] = "true" if value is True else "false" if value is False else "" if value is None else str(value)


def next_page_request(html: str, paged: int) -> tuple[str, dict]:
    """The (url, form data) that Fuusio's own 'Next' button sends to load page `paged`."""
    block = BeautifulSoup(html, "lxml").select_one(".sugar-calendar-event-list-block")
    common = json.loads(re.search(r"sc_frontend_blocks_common_obj\s*=\s*(\{.*?\});", html, re.S).group(1))
    payload = {
        "attributes": json.loads(block["data-attributes"]),
        "calendars": [], "venues": [], "speakers": [], "tags": [],
        "calendarsFilter": [], "venuesFilter": [], "speakersFilter": [], "tagsFilter": [],
        "featuredOnly": False, "search": "", "display": "grid",
        "day": int(block["data-ogday"]), "month": int(block["data-ogmonth"]),
        "year": int(block["data-ogyear"]),
        "visitor_tz_convert": 0, "visitor_tz": "Europe/Helsinki",
        "updateDisplay": False, "paged": paged, "action": "next_week",
    }
    form = {"action": AJAX_ACTION, "nonce": common["nonce"]}
    _flatten("block", payload, form)
    return common["ajax_url"], form


def extract(today: date) -> list[Event]:
    first = fetch_raw(SOURCE, PROGRAM_URL, today)
    events = parse(first)
    more, paged = next_enabled(first), 2
    while more and paged <= MAX_PAGES:
        url, form = next_page_request(first, paged)
        resp = post(url, data=form)
        body = resp.json()
        if not body.get("success"):
            raise RuntimeError(f"Fuusio page {paged}: unexpected response {resp.text[:200]}")
        save_raw(SOURCE, today, f"page{paged}", body["data"]["body"])
        events += parse(body["data"]["body"])
        more, paged = bool(body["data"].get("enable_next")), paged + 1
    return events
