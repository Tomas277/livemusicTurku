from datetime import date

from conftest import fixture
from pipeline.extract import kuka

TODAY = date(2026, 11, 13)


def events():
    return kuka.parse(fixture("kuka.html"), TODAY)


def test_parses_program_page():
    evs = events()
    assert len(evs) == 26
    assert evs[0].date == "2026-11-01" and evs[-1].date == "2026-12-16"


def test_titles_are_joined_without_markup_noise():
    titles = {e.title for e in events()}
    assert "Avolava – Open Mic Sunday" in titles  # letters are split across <span>s in the HTML
    assert "VHP Approt + DJ Konsta Eeva" in titles
    assert "DJ Reventeen" in titles


def test_start_time_from_excerpt():
    by_title = {e.title: e for e in events() if e.date in ("2026-11-14", "2026-11-15")}
    assert by_title["VHP Approt + DJ Konsta Eeva"].start == "16:00"
    assert by_title["Avolava – Open Mic Sunday"].start == "21:00"
    assert by_title["Avolava – Open Mic Sunday"].url.startswith("https://barkuka.fi/avolava")
