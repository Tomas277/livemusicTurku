from datetime import date
from pathlib import Path

from pipeline.extract import dynamo

HTML = (Path(__file__).parent / "fixtures" / "dynamo.html").read_text(encoding="utf-8")
TODAY = date(2026, 11, 13)


def events():
    return dynamo.parse(HTML, TODAY)


def test_parses_all_events():
    assert len(events()) == 23


def test_year_inferred_across_new_year():
    dates = [e["date"] for e in events()]
    assert dates[0] == "2026-11-12"  # yesterday's night is still listed
    assert dates[-1] == "2027-03-26"
    assert dates == sorted(dates)


def test_olga_details():
    olga = next(e for e in events() if e["title"] == "Olga")
    assert olga["date"] == "2026-11-13"
    assert olga["doors"] == "18:00"
    assert olga["start"] == "19:00"
    assert olga["age_limit"] == 18
    assert olga["url"] == "https://www.dynamoklubi.com/?page_id=17854"
