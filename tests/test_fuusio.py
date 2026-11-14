from conftest import fixture
from pipeline.extract import fuusio


def test_parses_both_pages():
    first = fuusio.parse(fixture("fuusio.html"))
    second = fuusio.parse(fixture("fuusio_page2.html"))
    assert (len(first), len(second)) == (20, 17)
    assert first[0].date == "2026-11-13"
    assert second[0].date == "2026-12-04" and second[-1].date.startswith("2027-02")


def test_room_names_are_removed_from_titles():
    titles = {e.title for e in fuusio.parse(fixture("fuusio.html")) + fuusio.parse(fixture("fuusio_page2.html"))}
    assert "Sivulliset, Annabelle, Sad Hill Tree" in titles  # was "... /Nirvana"
    assert "For My Pain... + Iterum Nata (solo)" in titles   # was "LIVESALI: For My Pain..."
    assert not any(t.endswith(("/Nirvana", "/Live", "/Level2", "/UG")) for t in titles)


def test_pagination_helpers():
    page = fixture("fuusio.html")
    assert fuusio.next_enabled(page)
    url, form = fuusio.next_page_request(page, 2)
    assert url == "https://fuusioturku.fi/wp-admin/admin-ajax.php"
    assert form["action"] == "sugar_calendar_event_list_block_update"
    assert form["nonce"] and form["block[paged]"] == "2" and form["block[action]"] == "next_week"
    assert (form["block[day]"], form["block[month]"], form["block[year]"]) == ("13", "11", "2026")
