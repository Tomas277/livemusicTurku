from datetime import date
from pathlib import Path

import duckdb

from pipeline.extract import dynamo
from pipeline.load import load
from pipeline.run import transform

HTML = (Path(__file__).parent / "fixtures" / "dynamo.html").read_text(encoding="utf-8")
TODAY = date(2026, 11, 13)


def build(today=TODAY):
    con = duckdb.connect()
    events = dynamo.parse(HTML, TODAY)
    load(con, "dynamo", events, today)
    transform(con, today)
    return con


def test_upcoming_drops_past_events_and_is_sorted():
    rows = build().execute("SELECT date, title FROM marts.upcoming_events").fetchall()
    assert len(rows) == 22  # the 12.11. gig is in the past
    assert rows[0][1] == "Olga"
    assert [r[0] for r in rows] == sorted(r[0] for r in rows)


def test_load_is_idempotent():
    con = build()
    load(con, "dynamo", dynamo.parse(HTML, TODAY), TODAY)  # same day again
    assert con.execute("SELECT count(*) FROM staging.events_raw").fetchone()[0] == 23


def test_duplicates_are_removed():
    con = duckdb.connect()
    events = dynamo.parse(HTML, TODAY)
    load(con, "dynamo", events + events[:3], TODAY)  # 3 duplicate rows
    transform(con, TODAY)
    assert con.execute("SELECT count(*) FROM int.events").fetchone()[0] == 23
