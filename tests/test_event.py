import pytest

from pipeline.event import COLUMNS, OPTIONAL, Event


def test_optional_fields_default_to_none_and_as_dict_has_every_column():
    d = Event(source="s", venue="v", title="t", date="2026-12-01", url="u").as_dict()
    assert tuple(d) == COLUMNS
    assert all(d[c] is None for c in OPTIONAL)
    assert {"doors", "start", "age_limit", "access", "availability"} <= OPTIONAL


def test_a_misspelled_or_missing_field_fails_immediately():
    with pytest.raises(TypeError):
        Event(source="s", venue="v", title="t", date="2026-12-01", url="u", availabilty="sold_out")
    with pytest.raises(TypeError):
        Event(source="s", venue="v", title="t", date="2026-12-01")  # no url
