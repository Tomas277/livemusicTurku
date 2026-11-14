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
    dates = [e.date for e in events()]
    assert dates[0] == "2026-11-12"  # yesterday's night is still listed
    assert dates[-1] == "2027-03-26"
    assert dates == sorted(dates)


def test_olga_details():
    olga = next(e for e in events() if e.title == "Olga")
    assert olga.date == "2026-11-13"
    assert olga.doors == "18:00"
    assert olga.start == "19:00"
    assert olga.age_limit == 18
    assert olga.url == "https://www.dynamoklubi.com/?page_id=17854"


def test_entry_info_from_the_description():
    by_title = {e.title: e for e in events()}
    assert by_title["YTK + guests"].access == "free"
    assert by_title["Olga"].availability == "sold_out"
    # Two floors with different terms: don't claim "free" for the whole night.
    assert by_title["Off the Rip vol. 8"].access is None


def test_one_bad_card_does_not_cost_the_rest(capsys):
    html = (Path(__file__).parent / "fixtures" / "dynamo.html").read_text(encoding="utf-8")
    assert "Live klo 20:30" in html
    broken = html.replace("Live klo 20:30", "Live klo 29:30", 1)  # 29:30 is not a time
    assert len(dynamo.parse(broken, TODAY)) == len(dynamo.parse(html, TODAY)) - 1
    assert "dynamo: skipped" in capsys.readouterr().err
