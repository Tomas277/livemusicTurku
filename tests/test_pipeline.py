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


def test_non_music_events_are_filtered_out():
    from pipeline.extract import fuusio, kuka
    con = duckdb.connect()
    load(con, "kuka", kuka.parse((Path(__file__).parent / "fixtures" / "kuka.html").read_text(encoding="utf-8"), TODAY), TODAY)
    load(con, "fuusio", fuusio.parse((Path(__file__).parent / "fixtures" / "fuusio.html").read_text(encoding="utf-8")), TODAY)
    transform(con, TODAY)
    titles = [r[0] for r in con.execute("SELECT title FROM int.events").fetchall()]
    for dropped in ("Pieni turkulainen kirjakerho", "BängerBINGO", "Kuka Mitä Häh?", "Levyraati",
                    "Runoviikon runoklubi", "Creative Coding- tapahtuma"):
        assert dropped not in titles
    assert "Avolava – Open Mic Sunday" in titles and "DJ Reventeen" in titles  # DJ and open mic stay


def test_runo_pattern_matches_only_at_word_start():
    def ev(title):
        return {"source": "t", "venue": "T", "title": title, "date": "2026-12-01",
                "doors": None, "start": None, "age_limit": None, "url": "u"}
    con = duckdb.connect()
    load(con, "t", [ev("Bruno Mars Tribute"), ev("Runoilta"), ev("Kuka Runoklubi")], TODAY)
    transform(con, TODAY)
    kept = {r[0] for r in con.execute("SELECT title FROM int.events").fetchall()}
    assert kept == {"Bruno Mars Tribute"}
