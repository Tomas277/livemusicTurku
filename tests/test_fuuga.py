from datetime import date

from conftest import fixture
from pipeline.extract import fuuga

TODAY = date(2026, 11, 14)


def events():
    return fuuga.parse(fixture("fuuga.html"), TODAY)


def test_parses_listing_page_and_drops_helsinki_guest_concert():
    evs = events()
    assert len(evs) == 9  # 10 listed, one is a TFO guest concert in Helsinki
    assert all(e["venue"] == "Fuuga" for e in evs)
    assert evs[0]["date"] == "2026-11-13" and evs[0]["start"] == "18:00"


def test_sold_out_prefix_and_room_names_are_removed():
    titles = {e["title"] for e in events()}
    assert "Avajaiskonsertti" in titles
    assert not any(t.lower().startswith("loppuunmyyty") for t in titles)


def test_listing_past_the_last_page_is_empty():
    assert fuuga.parse(fixture("fuuga_end.html"), TODAY) == []
