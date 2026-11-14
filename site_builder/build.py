import json
import shutil
from datetime import date
from itertools import groupby
from pathlib import Path

import duckdb
from jinja2 import Environment, FileSystemLoader, select_autoescape

from site_builder.i18n import (MONTHS_NOMINATIVE, MONTHS_SHORT, STRINGS, WEEKDAYS, WEEKDAYS_SHORT,
                               format_age, format_day, format_month)

ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"
SITE = ROOT / "site"
# One colour per venue, so a glance at the dots tells you where a gig is.
VENUE_COLORS = ["#e4452b", "#2f7de1", "#1f9d6c", "#c98a0b", "#8e55d6",
                "#d4478f", "#0e9aa7", "#7a8b1f", "#b25b2a"]


def read_events(con) -> list[dict]:
    cur = con.execute("SELECT venue, title, date, doors, start, age_limit, url, access, availability "
                      "FROM marts.upcoming_events")
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def render(events: list[dict], built_on: date, out: Path = SITE) -> None:
    if not events:
        raise ValueError("No upcoming events: refusing to build an empty site")
    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape())
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "static", out / "static")

    venues = sorted({e["venue"] for e in events})
    colors = {v: VENUE_COLORS[i % len(VENUE_COLORS)] for i, v in enumerate(venues)}
    for lang, t in STRINGS.items():
        months = [
            {"key": f"{k[0]}-{k[1]:02d}", "label": format_month(evs[0]["date"], lang),
             "events": [dict(e, age=format_age(e["age_limit"], lang), color=colors[e["venue"]],
                             dow=WEEKDAYS_SHORT[lang][e["date"].weekday()],
                             mon=MONTHS_SHORT[lang][e["date"].month - 1],
                             label=format_day(e["date"], lang)) for e in evs]}
            for k, evs in ((k, list(g)) for k, g in groupby(events, key=lambda e: (e["date"].year, e["date"].month)))
        ]
        js_strings = {
            "weekdays": WEEKDAYS_SHORT[lang], "weekdays_long": WEEKDAYS[lang], "months": MONTHS_NOMINATIVE[lang],
            **{k: t[k] for k in ("today", "tomorrow", "empty", "empty_week", "empty_day", "gigs", "prev", "next")},
        }
        page = env.get_template("index.html").render(
            t=t, lang=lang, months=months, venues=[{"name": v, "color": colors[v]} for v in venues],
            built_on=built_on.isoformat(), js_strings=js_strings,
            dateline=format_day(built_on, lang) + f" {built_on.year}")
        (out / lang).mkdir(parents=True, exist_ok=True)
        (out / lang / "index.html").write_text(page, encoding="utf-8")

    (out / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Live Music Turku</title>'
        '<script>location.replace(navigator.language.startsWith("fi") ? "fi/" : "en/")</script>'
        '<noscript><a href="fi/">Suomeksi</a> · <a href="en/">English</a></noscript>',
        encoding="utf-8")
    payload = [dict(e, date=e["date"].isoformat()) for e in events]
    (out / "upcoming.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    events = read_events(con)
    render(events, date.today())
    print(f"site/: {len(events)} events, languages: {', '.join(STRINGS)}")


if __name__ == "__main__":
    main()
