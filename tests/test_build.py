from datetime import date

from site_builder.build import render
from site_builder.i18n import format_age, format_day

EVENTS = [
    {"venue": "Dynamo", "title": "Olga <b>", "date": date(2026, 11, 14), "doors": "20:00",
     "start": "20:30", "age_limit": 18, "url": "https://example.com/olga"},
    {"venue": "Apollo", "title": "Stam1na", "date": date(2026, 12, 12), "doors": None,
     "start": None, "age_limit": None, "url": "https://example.com/stam1na"},
]


def test_renders_both_languages(tmp_path):
    render(EVENTS, date(2026, 11, 14), tmp_path)
    fi = (tmp_path / "fi" / "index.html").read_text(encoding="utf-8")
    en = (tmp_path / "en" / "index.html").read_text(encoding="utf-8")
    assert "lauantai 14. marraskuuta" in fi and "K18" in fi and "Ovet 20:00" in fi
    assert "Saturday 14 November" in en and "18+" in en and "Doors 20:00" in en
    assert (tmp_path / "static" / "app.js").exists()
    assert (tmp_path / "upcoming.json").exists()


def test_titles_are_escaped(tmp_path):
    render(EVENTS, date(2026, 11, 14), tmp_path)
    html = (tmp_path / "en" / "index.html").read_text(encoding="utf-8")
    assert "Olga &lt;b&gt;" in html and "Olga <b>" not in html


def test_format_helpers():
    assert format_day(date(2026, 11, 14), "fi") == "lauantai 14. marraskuuta"
    assert format_age(None, "fi") is None
