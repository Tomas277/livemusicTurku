import json
import shutil
from datetime import date
from itertools import groupby
from pathlib import Path

import duckdb
from jinja2 import Environment, FileSystemLoader, select_autoescape

from site_builder.i18n import STRINGS, format_age, format_day

ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"
SITE = ROOT / "site"


def read_events(con) -> list[dict]:
    cur = con.execute("SELECT venue, title, date, doors, start, age_limit, url "
                      "FROM marts.upcoming_events")
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def render(events: list[dict], built_on: date, out: Path = SITE) -> None:
    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape())
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "static", out / "static")

    venues = sorted({e["venue"] for e in events})
    for lang, t in STRINGS.items():
        days = [
            {"date": d.isoformat(), "label": format_day(d, lang),
             "events": [dict(e, age=format_age(e["age_limit"], lang)) for e in evs]}
            for d, evs in groupby(events, key=lambda e: e["date"])
        ]
        page = env.get_template("index.html").render(
            t=t, lang=lang, days=days, venues=venues, built_on=built_on.isoformat())
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
