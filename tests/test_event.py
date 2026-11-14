from dataclasses import fields

import pytest

from pipeline.event import COLUMNS, HISTORY_TYPES, SQL_TYPES, Event


def make(**kw):
    return Event(**{"source": "s", "venue": "v", "title": "t", "date": "2026-12-01", "url": "u", **kw})


def test_optional_fields_default_to_none():
    e = make()
    assert tuple(f.name for f in fields(e)) == COLUMNS
    assert {f.name for f in fields(e) if getattr(e, f.name) is None} == {
        "doors", "start", "age_limit", "access", "availability"}


def test_bad_values_fail_where_the_event_is_made():
    for bad in ({"title": " "}, {"venue": ""}, {"url": ""}, {"date": "2026-13-45"}, {"date": "14.11.2026"}, {"start": "7pm"}, {"doors": "9:00"}, {"start": "29:00"}, {"doors": "12:61"},
                {"age_limit": "K12"}, {"age_limit": True}, {"access": "paid"}, {"availability": "full"}):
        with pytest.raises(ValueError):
            make(**bad)
    make(age_limit=18, start="19:30", doors="18:00", access="free", availability="few")


def test_a_misspelled_or_missing_field_fails_immediately():
    with pytest.raises(TypeError):
        Event(source="s", venue="v", title="t", date="2026-12-01", url="u", availabilty="sold_out")
    with pytest.raises(TypeError):
        Event(source="s", venue="v", title="t", date="2026-12-01")  # no url


def test_every_event_field_has_a_database_type():
    assert set(SQL_TYPES) == set(COLUMNS)
    assert list(HISTORY_TYPES) == [*SQL_TYPES, "first_seen", "last_seen"]


def test_make_event_skips_and_logs_a_bad_gig(capsys):
    from pipeline.event import add_event, make_event
    assert make_event(source="s", venue="v", title="Ok", date="2026-12-01", url="u").title == "Ok"
    assert make_event(source="s", venue="v", title="", date="2026-12-01", url="https://x/e") is None
    assert "s: skipped 'https://x/e' - title is empty" in capsys.readouterr().err
    events = []
    add_event(events, source="s", venue="v", title="Bad", date="nope", url="u")
    assert events == [] and "skipped 'Bad'" in capsys.readouterr().err
