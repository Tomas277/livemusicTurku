from datetime import date

from pipeline.checks import check_events
from pipeline.event import Event

TODAY = date(2026, 11, 13)


def ev(title="A", day="2026-12-01", **kw):
    return Event(**{"source": "s", "title": title, "date": day, "venue": "V", "url": "https://x", **kw})


def test_good_scrape_passes():
    assert check_events("s", [ev("A"), ev("B")], TODAY, previous_upcoming=2) == []


def test_missing_required_field():
    problems = check_events("s", [ev(url="")], TODAY, 0)
    assert len(problems) == 1 and "missing url" in problems[0]


def test_dates_outside_the_expected_range():
    assert check_events("s", [ev(day="2025-01-01")], TODAY, 0)            # parsed with the wrong year
    assert check_events("s", [ev(day="2028-01-01")], TODAY, 0)
    assert check_events("s", [ev(day="2026-11-01")], TODAY, 0) == []      # a recent past gig is fine


def test_big_drop_in_gig_count_is_flagged():
    few = [ev(str(i), day="2026-12-01") for i in range(3)]
    assert "probably broke" in check_events("s", few, TODAY, previous_upcoming=20)[0]
    ok = [ev(str(i)) for i in range(11)]
    assert check_events("s", ok, TODAY, previous_upcoming=20) == []        # a normal fluctuation


def test_zero_gigs_after_having_some_is_flagged_even_when_small():
    assert "no upcoming gigs" in check_events("s", [], TODAY, previous_upcoming=2)[0]
    assert check_events("s", [], TODAY, previous_upcoming=0) == []         # first run, nothing to compare


def test_many_problems_are_summarised():
    bad = [ev(str(i), url="") for i in range(9)]
    problems = check_events("s", bad, TODAY, 0)
    assert len(problems) == 6 and "4 more" in problems[-1]


def test_accept_drop_skips_only_the_count_comparison():
    few = [ev(str(i)) for i in range(3)]
    assert check_events("s", few, TODAY, previous_upcoming=20, accept_drop=True) == []
    assert check_events("s", [], TODAY, previous_upcoming=20, accept_drop=True) == []
    assert "missing title" in check_events("s", [ev(title="")], TODAY, 20, accept_drop=True)[0]
