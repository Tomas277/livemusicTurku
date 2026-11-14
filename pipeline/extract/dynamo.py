import re
from datetime import date

from bs4 import BeautifulSoup

from pipeline.access import classify
from pipeline.dates import find_time, infer_date
from pipeline.event import Event

SOURCE = "dynamo"
VENUE = "Dynamo"
BASE_URL = "https://www.dynamoklubi.com/"
PROGRAM_URL = BASE_URL + "ohjelma"


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
        links = " ".join(a.get("href", "") for a in excerpt.select("a"))  # ticket shop links hide in hrefs
        access, availability = classify(f"{text} {links}")
        if access == "free" and "UP:" in text and "DOWN:" in text:
            access = None  # two floors with their own entry terms: "free" may only hold for one of them
        link = re.search(r'navigateToURL\("([^"]+)"', block.get("onclick", ""))
        events.append(Event(
            source=SOURCE,
            venue=VENUE,
            title=title_tag.get_text(" ", strip=True),
            date=infer_date(int(m.group(1)), int(m.group(2)), today,
                               day_name.get_text(strip=True)).isoformat(),
            doors=find_time(r"ovet\s*klo", text),
            start=find_time(r"live\s*klo", text),
            age_limit=int(age.group(1)) if age else None,
            access=access,
            availability=availability,
            url=BASE_URL + link.group(1) if link else PROGRAM_URL,
        ).as_dict())
    return events


def extract(today: date) -> list[dict]:
    from pipeline.fetch import fetch_raw
    return parse(fetch_raw(SOURCE, PROGRAM_URL, today), today)
