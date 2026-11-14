"""Work out from a venue's own wording whether entry is free or needs a ticket, and whether it is sold out.

Only Fuuga publishes how many tickets are left; for everyone else we can say "tickets",
"free entry" or "sold out" when the page says so, and otherwise stay silent (None).
"""
import re

FREE = re.compile(r"vapaa\s+p[aä][aä]sy|p[aä][aä]sy\s+vapaa|ilmainen|free\s+(?:entry|admission)", re.I)
SOLD_OUT = re.compile(r"loppuunmyyty|sold[\s-]?out", re.I)
TICKETS_LINE = re.compile(r"\bliput\s*:|\btickets\s*:", re.I)
PRICE = re.compile(r"\d\s?€|€\s?\d")
TICKET_SELLER = re.compile(r"lippu\.fi|tiketti\.fi|ticketmaster|livex\.fi|lippupiste|kide\.app|eventbrite|bilettikauppa|biletti\.fi", re.I)


def classify(text: str, ticket_link: bool = False) -> tuple[str | None, str | None]:
    """Return (access, availability) for one gig from its description text."""
    if SOLD_OUT.search(text):
        return "tickets", "sold_out"
    # A ticket seller or a "Liput:" line is decisive. A bare price is not: "free entry, bottle of bubbly 16 EUR"
    # is about drinks, so a price only means tickets when nothing says the entry is free.
    if ticket_link or TICKET_SELLER.search(text) or TICKETS_LINE.search(text):
        return "tickets", None
    if FREE.search(text):
        return "free", None
    return ("tickets", None) if PRICE.search(text) else (None, None)
