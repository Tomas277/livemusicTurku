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
    # Only "sold out" gets a badge; free entry, tickets and unknown all show nothing.
    assert 'class="status' not in fi and "Vapaa pääsy" not in fi and "Liput" not in fi
    sold = [dict(EVENTS[0], availability="sold_out")]
    render(sold, date(2026, 11, 14), tmp_path)
    assert 'class="status sold_out">Loppuunmyyty' in (tmp_path / "fi" / "index.html").read_text(encoding="utf-8")


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


def test_main_builds_from_the_history_csv_alone(tmp_path, monkeypatch):
    from datetime import timedelta

    from pipeline import history
    from pipeline.event import Event
    from pipeline.load import load
    from site_builder import build
    from conftest import empty_con

    today = date.today()
    con = empty_con()
    load(con, "dynamo", [Event(source="dynamo", venue="Dynamo", title="Future gig",
                               date=(today + timedelta(days=5)).isoformat(), url="u")], today)
    from pipeline.sql import transform
    transform(con, today)
    history.save(con, tmp_path / "history.csv")

    monkeypatch.setattr(history, "DEFAULT_PATH", tmp_path / "history.csv")
    built = []
    monkeypatch.setattr(build, "render", lambda events, built_on: built.append(events))
    build.main()  # needs nothing but the history CSV
    assert [e["title"] for e in built[0]] == ["Future gig"]


def test_pages_point_search_engines_at_both_languages(tmp_path):
    from site_builder.build import SITE_URL
    render(EVENTS, date(2026, 11, 14), tmp_path)
    fi = (tmp_path / "fi" / "index.html").read_text(encoding="utf-8")
    assert f'rel="canonical" href="{SITE_URL}fi/"' in fi
    assert f'hreflang="en" href="{SITE_URL}en/"' in fi and 'hreflang="x-default"' in fi
