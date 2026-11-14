from datetime import date

from conftest import fixture
from pipeline.extract import apollo

TODAY = date(2026, 11, 13)


def test_parses_gig_listing():
    evs = apollo.parse(fixture("apollo.html"), TODAY)
    assert len(evs) == 13
    assert evs[0].title == "Aliisa Syrjä" and evs[0].date == "2026-11-13"
    assert evs[0].url == "https://apolloturku.fi/keikat/151/aliisa-syrja"
    assert evs[-1].date == "2027-04-09"  # year rolls over


def test_two_night_party_band_becomes_two_events():
    evs = apollo.parse(fixture("apollo_bilebandi.html"), TODAY, apollo.PAGES["bilebandi"])
    gen_y = sorted(e.date for e in evs if e.title == "Generation Y (SWE)")
    assert gen_y == ["2026-11-13", "2026-11-14"]
    assert all(e.url.startswith("https://apolloturku.fi/bilebandi/") for e in evs)


def test_every_gig_with_a_shop_button_needs_tickets():
    evs = apollo.parse(fixture("apollo.html"), TODAY)
    assert evs and {e.access for e in evs} == {"tickets"}
