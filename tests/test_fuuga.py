import json
from datetime import date

from conftest import fixture
from pipeline.event import Event
from pipeline.extract import fuuga

TODAY = date(2026, 11, 14)


def events(name="fuuga.json"):
    return fuuga.parse(json.loads(fixture(name)), TODAY)


def test_parses_a_page_of_events():
    evs = events()
    assert len(evs) == 9
    assert evs[0].title == "TFO: Avajaiskonsertti"
    assert evs[0].date == "2026-11-14" and evs[0].start == "14:00"
    assert evs[0].venue == "Fuuga"  # "Konserttisali" is a room, not a venue
    assert evs[0].url.startswith("https://www.musiikkitalofuuga.fi/events/")


def test_uses_the_real_night_not_the_first_night_of_a_run():
    muumit = next(e for e in events() if e.title.startswith("Muumit"))
    assert muumit.date == "2026-11-15"  # the API's "date" field says 14.11. for this one


def test_html_entities_in_titles_are_decoded():
    titles = {e.title for e in events()}
    assert "TMJ: Red Nose Company & Meta4: Voces – Sisäisiä ääniä" in titles


def test_talk_shows_and_ballet_are_dropped_and_other_venues_keep_their_name():
    evs = events("fuuga_misc.json")
    titles = {e.title for e in evs}
    assert not any("Keikarit" in t or "JOUTSENLAMPI" in t for t in titles)
    assert {e.venue for e in evs} == {"Martinkirkko", "Sigyn-sali"}


def test_empty_page_means_the_end():
    assert events("fuuga_end.json") == []


def _ev(title, start="14:00"):
    return Event(source="fuuga", venue="Fuuga", title=title, date="2026-11-14", start=start, url="u")


def test_same_concert_listed_by_two_organizers_is_shown_once():
    out = fuuga.dedupe([_ev("Avajaiskonsertti"), _ev("TFO: Avajaiskonsertti")])
    assert [e.title for e in out] == ["TFO: Avajaiskonsertti"]


def test_same_title_at_different_times_is_kept():
    assert len(fuuga.dedupe([_ev("Muumit", "14:00"), _ev("Muumit", "17:00")])) == 2


def test_ticket_availability_comes_from_the_status_colours():
    by_title = {e.title: e for e in events()}
    assert by_title["TFO: Avajaiskonsertti"].availability == "sold_out"
    assert by_title["Muumit Pyrstötähteä etsimässä"].availability == "few"
    assert by_title["Viktoria Tolstoy & Jacob Karlzon – Who We Are"].availability == "available"
    assert {e.access for e in events()} == {"tickets"}


def test_normalize_time():
    from pipeline.dates import normalize_time
    assert normalize_time("9:30") == "09:30" and normalize_time("19:00 - 21:00") == "19:00"
    assert normalize_time("") is None and normalize_time("illalla") is None
