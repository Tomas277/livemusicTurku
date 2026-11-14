from datetime import date

from site_builder.build import render
from site_builder.i18n import format_age, format_day, format_month

EVENTS = [
    {"venue": "Dynamo", "title": "Olga <b>", "date": date(2026, 11, 14), "doors": "20:00",
     "start": "20:30", "age_limit": 18, "url": "https://example.com/olga",
     "access": "tickets", "availability": "few"},
    {"venue": "Apollo", "title": "Stam1na", "date": date(2026, 12, 12), "doors": None,
     "start": None, "age_limit": None, "url": "https://example.com/stam1na",
     "access": "free", "availability": None},
]


def test_renders_both_languages(tmp_path):
    render(EVENTS, date(2026, 11, 14), tmp_path)
    fi = (tmp_path / "fi" / "index.html").read_text(encoding="utf-8")
    en = (tmp_path / "en" / "index.html").read_text(encoding="utf-8")
    assert "Marraskuu 2026" in fi and "Joulukuu 2026" in fi and "K18" in fi and "Ovet 20:00" in fi
    assert "November 2026" in en and "December 2026" in en and "18+" in en and "Doors 20:00" in en
    assert 'data-view="calendar"' in en and "--vc: #" in en
    assert (tmp_path / "static" / "app.js").exists()
    assert (tmp_path / "upcoming.json").exists()


def test_entry_badges(tmp_path):
    render(EVENTS, date(2026, 11, 14), tmp_path)
    fi = (tmp_path / "fi" / "index.html").read_text(encoding="utf-8")
    en = (tmp_path / "en" / "index.html").read_text(encoding="utf-8")
    assert "Vähän lippuja jäljellä" in fi and "Vapaa pääsy" in fi
    assert "Few tickets left" in en and "Free entry" in en


def test_titles_are_escaped(tmp_path):
    render(EVENTS, date(2026, 11, 14), tmp_path)
    html = (tmp_path / "en" / "index.html").read_text(encoding="utf-8")
    assert "Olga &lt;b&gt;" in html and "Olga <b>" not in html


def test_format_helpers():
    assert format_day(date(2026, 11, 14), "fi") == "lauantai 14. marraskuuta"
    assert format_month(date(2026, 11, 14), "fi") == "Marraskuu 2026"
    assert format_age(None, "fi") is None


def test_refuses_to_build_an_empty_site(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        render([], date(2026, 11, 14), tmp_path)
