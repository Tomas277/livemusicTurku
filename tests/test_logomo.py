from datetime import date

from conftest import fixture
from pipeline.extract import logomo

TODAY = date(2026, 11, 14)
URL = "https://logomo.fi/tapahtuma/anssi-kela-nummela-25-vuotisjuhlakonserttikiertue"


def test_parses_event_page():
    ev = logomo.parse_event(fixture("logomo_event.html"), URL, TODAY)
    assert ev.title.startswith("ANSSI KELA")
    assert ev.date == "2026-11-18" and ev.start == "19:00"
    assert ev.venue == "Logomo" and ev.url == URL


def test_event_without_start_time_still_parses():
    ev = logomo.parse_event(fixture("logomo_event_notime.html"), URL, TODAY)
    assert ev.title.startswith("APULANTA")
    assert ev.date == "2026-12-12" and ev.start is None


def test_past_events_are_dropped():
    assert logomo.parse_event(fixture("logomo_event.html"), URL, date(2026, 11, 19)) is None


def test_page_without_event_details_is_skipped():
    assert logomo.parse_event("<html><body><h1>Hello</h1></body></html>", URL, TODAY) is None


def test_sitemap_urls():
    urls = logomo.event_urls(fixture("logomo_sitemap.xml"))
    assert len(urls) == 5 and all(u.startswith("https://logomo.fi/tapahtuma/") for u in urls)


def test_ticket_shop_link_means_tickets():
    ev = logomo.parse_event(fixture("logomo_event.html"), URL, TODAY)
    assert ev.access == "tickets" and ev.availability is None


def test_sold_out_marker_is_kept_out_of_the_title():
    html = fixture("logomo_event.html").replace("ANSSI KELA – NUMMELA 25-VUOTISJUHLAKONSERTTIKIERTUE",
                                               "ANSSI KELA – NUMMELA 25-VUOTISJUHLAKONSERTTIKIERTUE *LOPPUUNMYYTY*")
    ev = logomo.parse_event(html, URL, TODAY)
    assert ev.availability == "sold_out"
    assert ev.title == "ANSSI KELA – NUMMELA 25-VUOTISJUHLAKONSERTTIKIERTUE"


def test_age_limit_is_a_number():
    html = fixture("logomo_event.html").replace("Ikärajaton", "Ikäraja: K18 (anniskelualuetta)")
    assert logomo.parse_event(html, URL, TODAY).age_limit == 18
    assert logomo.parse_event(fixture("logomo_event.html"), URL, TODAY).age_limit is None
