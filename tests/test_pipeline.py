import pytest
from datetime import date
from pathlib import Path

import duckdb

from conftest import empty_con
from pipeline.event import Event
from pipeline.extract import dynamo
from pipeline.load import load
from pipeline.run import transform

HTML = (Path(__file__).parent / "fixtures" / "dynamo.html").read_text(encoding="utf-8")
TODAY = date(2026, 11, 13)


def build(today=TODAY):
    con = empty_con()
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
    con = empty_con()
    events = dynamo.parse(HTML, TODAY)
    load(con, "dynamo", events + events[:3], TODAY)  # 3 duplicate rows
    transform(con, TODAY)
    assert con.execute("SELECT count(*) FROM int.events").fetchone()[0] == 23


def test_non_music_events_are_filtered_out():
    from pipeline.extract import fuusio, kuka
    con = empty_con()
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
        return Event(source="t", venue="T", title=title, date="2026-12-01", url="u")
    con = empty_con()
    load(con, "t", [ev("Bruno Mars Tribute"), ev("Runoilta"), ev("Kuka Runoklubi")], TODAY)
    transform(con, TODAY)
    kept = {r[0] for r in con.execute("SELECT title FROM int.events").fetchall()}
    assert kept == {"Bruno Mars Tribute"}


def test_one_broken_source_does_not_stop_the_others(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace

    from pipeline import run

    def good(today):
        return [Event(source="good", venue="G", title="Fine gig", date="2026-12-01", start="19:00",
                      age_limit=18, url="u")]

    def raises(today):
        raise RuntimeError("site is down")

    def bad_value(today):  # Event refuses a string where a number belongs
        return [Event(source="bad", venue="B", title="Odd gig", date="2026-12-01", url="u", age_limit="K12")]

    monkeypatch.setattr(run, "SOURCES", {"good": SimpleNamespace(extract=good),
                                         "raises": SimpleNamespace(extract=raises),
                                         "bad": SimpleNamespace(extract=bad_value)})
    monkeypatch.setattr(run, "HISTORY_CSV", tmp_path / "history.csv")
    monkeypatch.setattr(run, "date", SimpleNamespace(today=lambda: TODAY))
    with pytest.raises(SystemExit) as exit_info:
        run.main()
    assert exit_info.value.code == 1
    err = capsys.readouterr().err
    assert "raises: FAILED" in err and "bad: FAILED - ValueError" in err
    assert "Fine gig" in (tmp_path / "history.csv").read_text(encoding="utf-8")


def test_a_failed_load_leaves_staging_as_it_was():
    from pipeline.load import load
    con = empty_con()

    def gig(title):
        return Event(source="t", venue="T", title=title, date="2026-12-01", url="u")

    load(con, "t", [gig("First"), gig("Second")], TODAY)
    broken = gig("Broken")
    object.__setattr__(broken, "age_limit", "not a number")  # slips past Event's own check
    with pytest.raises(Exception):
        load(con, "t", [gig("Replacement"), broken], TODAY)  # same source and day: replaces the rows
    assert sorted(r[0] for r in con.execute("SELECT title FROM staging.events_raw").fetchall()) == ["First", "Second"]
