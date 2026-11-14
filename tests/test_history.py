from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import duckdb

from pipeline import history
from pipeline.event import Event
from pipeline.load import load
from pipeline.run import transform

D1 = date(2026, 11, 13)
D2 = D1 + timedelta(days=1)


def ev(title, day="2026-12-01", source="dynamo", venue="Dynamo"):
    return Event(source=source, venue=venue, title=title, date=day, doors="20:00", age_limit=18,
                 url=f"https://x/{title}", access="tickets", availability="few")


def run_day(con, today, events_by_source):
    """One pipeline day: load each successful source, then transform."""
    for source, events in events_by_source.items():
        load(con, source, events, today)
    transform(con, today)


def site(con):
    return sorted(r[0] for r in con.execute("SELECT title FROM marts.upcoming_events").fetchall())


def rows(con):
    return {r[0]: r[1:] for r in con.execute(
        "SELECT title, first_seen, last_seen FROM history.events_history").fetchall()}


def new_con():
    con = duckdb.connect()
    history.restore(con, Path("does-not-exist.csv"))  # creates the empty history table
    return con


def test_first_seen_is_kept_and_last_seen_moves():
    con = new_con()
    run_day(con, D1, {"dynamo": [ev("A")]})
    run_day(con, D2, {"dynamo": [ev("A")]})
    assert rows(con)["A"] == (D1, D2)


def test_gig_that_vanishes_stays_in_history_but_leaves_the_site():
    con = new_con()
    run_day(con, D1, {"dynamo": [ev("A"), ev("B")]})
    run_day(con, D2, {"dynamo": [ev("A")]})
    assert rows(con)["B"] == (D1, D1)       # remembered, last seen yesterday
    assert site(con) == ["A"]               # but no longer shown


def test_failed_source_keeps_its_last_good_gigs_on_the_site():
    con = new_con()
    run_day(con, D1, {"dynamo": [ev("A")], "kuka": [ev("K", source="kuka", venue="Kuka")]})
    run_day(con, D2, {"kuka": [ev("K", source="kuka", venue="Kuka")]})  # dynamo failed today
    assert site(con) == ["A", "K"]
    assert rows(con)["A"] == (D1, D1)       # not marked as seen today


def test_stale_source_is_dropped_after_a_week():
    con = new_con()
    run_day(con, D1, {"dynamo": [ev("A")]})
    run_day(con, D1 + timedelta(days=7), {})
    assert site(con) == ["A"]
    run_day(con, D1 + timedelta(days=8), {})
    assert site(con) == []


def test_same_day_rerun_changes_nothing():
    con = new_con()
    run_day(con, D1, {"dynamo": [ev("A"), ev("B")]})
    before = con.execute("SELECT * FROM history.events_history ORDER BY title").fetchall()
    run_day(con, D1, {"dynamo": [ev("A"), ev("B")]})
    assert con.execute("SELECT * FROM history.events_history ORDER BY title").fetchall() == before


def test_csv_round_trip(tmp_path):
    con = new_con()
    run_day(con, D1, {"dynamo": [ev('Band, "The" Best'), ev("B")]})
    path = tmp_path / "w" / "events_history.csv"
    history.save(con, path)

    other = duckdb.connect()
    history.restore(other, path)
    cols = "source, venue, title, date, doors, start, age_limit, url, access, availability, first_seen, last_seen"
    q = f"SELECT {cols} FROM history.events_history ORDER BY title"
    assert other.execute(q).fetchall() == con.execute(q).fetchall()
    assert other.execute("SELECT typeof(doors), typeof(date) FROM history.events_history LIMIT 1").fetchone() \
        == ("VARCHAR", "DATE")


def test_restore_without_a_file_starts_empty(tmp_path):
    con = duckdb.connect()
    history.restore(con, tmp_path / "missing.csv")
    assert con.execute("SELECT count(*) FROM history.events_history").fetchone()[0] == 0


def test_previous_upcoming_count():
    con = new_con()
    run_day(con, D1, {"dynamo": [ev("A"), ev("B"), ev("Old", day="2026-11-01")]})
    assert history.previous_upcoming_count(con, "dynamo", D1) == 2   # the past gig doesn't count
    assert history.previous_upcoming_count(con, "kuka", D1) == 0


def test_restore_reads_a_history_file_from_before_access_columns_existed(tmp_path):
    path = tmp_path / "old.csv"
    path.write_text("source,venue,title,date,doors,start,age_limit,url,first_seen,last_seen\n"
                    "kuka,Kuka,Old gig,2026-12-01,,21:00,,https://x,2026-11-13,2026-11-13\n", encoding="utf-8")
    con = duckdb.connect()
    history.restore(con, path)
    assert con.execute("SELECT title, access, availability FROM history.events_history").fetchall() \
        == [("Old gig", None, None)]


def test_access_and_availability_reach_the_site_and_update_on_rescrape():
    con = new_con()
    run_day(con, D1, {"dynamo": [ev("A")]})
    run_day(con, D2, {"dynamo": [replace(ev("A"), availability="sold_out")]})
    assert con.execute("SELECT access, availability FROM marts.upcoming_events").fetchall() == [("tickets", "sold_out")]


def test_a_retitled_gig_keeps_its_identity():
    con = new_con()
    run_day(con, D1, {"dynamo": [ev("Band X")]})
    run_day(con, D2, {"dynamo": [ev("BAND  X!"), ev("Ä-Band Ö")]})
    assert rows(con) == {"BAND  X!": (D1, D2), "Ä-Band Ö": (D2, D2)}
    run_day(con, D2 + timedelta(days=1), {"dynamo": [ev("ä band ö")]})
    assert rows(con)["ä band ö"][0] == D2  # umlauts count as letters; the gig is still the same
    assert site(con) == ["ä band ö"]


def test_unknown_csv_column_gives_a_clear_error(tmp_path):
    import pytest
    path = tmp_path / "h.csv"
    path.write_text("title,mood\nA,happy\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown column.*mood"):
        history.restore(duckdb.connect(), path)


def test_restore_then_save_leaves_the_file_byte_identical(tmp_path):
    first = tmp_path / "a.csv"
    con = new_con()
    run_day(con, D1, {"dynamo": [ev('Band, "The" Best'), ev("Äiti", "2026-12-02"), ev("B", "2026-12-01")]})
    history.save(con, first)
    again = tmp_path / "b.csv"
    other = duckdb.connect()
    history.restore(other, first)
    history.save(other, again)
    assert again.read_bytes() == first.read_bytes()  # no git diff churn from a run that changes nothing
