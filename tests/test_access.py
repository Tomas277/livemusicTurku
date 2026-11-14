from pipeline.access import classify


def test_free_entry_even_when_drinks_have_prices():
    text = "Ovet klo 22 Vapaa pääsy koko illan! Skumppapullo 16€ ja hanaolut 5,5€"
    assert classify(text) == ("free", None)


def test_ticket_seller_or_liput_line_means_tickets():
    assert classify("Liput: Lippu.fi à 22€ (+tilausmaksu). Ovelta 24€") == ("tickets", None)
    assert classify("Info", ticket_link=True) == ("tickets", None)


def test_sold_out_wins():
    assert classify("KEIKKA LOPPUUNMYYTY : Ovet klo 20:30 Liput: Lippu.fi") == ("tickets", "sold_out")
    assert classify("Sold out!") == ("tickets", "sold_out")


def test_bare_price_is_an_entry_fee_and_silence_stays_unknown():
    assert classify("Sisään 3€ sis. haalarimerkki") == ("tickets", None)
    assert classify("Karaoke ja DJ") == (None, None)
