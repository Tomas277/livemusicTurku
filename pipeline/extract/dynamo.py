import re
from datetime import date

from bs4 import BeautifulSoup

from pipeline.dates import infer_date

SOURCE = "dynamo"
VENUE = "Dynamo"
BASE_URL = "https://www.dynamoklubi.com/"
PROGRAM_URL = BASE_URL + "ohjelma"

_TIME = r"(\d{1,2})(?:[:.](\d{2}))?"


def _find_time(pattern: str, text: str) -> str | None:
    m = re.search(pattern + r"\s*klo\s*" + _TIME, text, re.IGNORECASE)
    if not m:
        return None
    return f"{int(m.group(1)):02d}:{m.group(2) or '00'}"


def parse(html: str, today: date) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    events = []
    for block in soup.select("div.content_item_article_link"):
        day_name = block.select_one(".day-name")
        day_number = block.select_one(".day-number")
        excerpt = block.select_one(".content_item_excerpt")
        if not (day_name and day_number and excerpt):
            continue
        m = re.match(r"(\d{1,2})\.(\d{1,2})\.", day_number.get_text(strip=True))
        title_tag = excerpt.find("strong")
        if not (m and title_tag):
            continue
        text = excerpt.get_text(" ", strip=True)
        age = re.search(r"\bK-?(\d{1,2})\b", text)
        link = re.search(r'navigateToURL\("([^"]+)"', block.get("onclick", ""))
        events.append({
            "source": SOURCE,
            "venue": VENUE,
            "title": title_tag.get_text(" ", strip=True),
            "date": infer_date(int(m.group(1)), int(m.group(2)), today,
                               day_name.get_text(strip=True)).isoformat(),
            "doors": _find_time("ovet", text),
            "start": _find_time("live", text),
            "age_limit": int(age.group(1)) if age else None,
            "url": BASE_URL + link.group(1) if link else PROGRAM_URL,
        })
    return events


def extract(today: date) -> list[dict]:
    from pipeline.fetch import fetch_raw
    return parse(fetch_raw(SOURCE, PROGRAM_URL, today), today)
