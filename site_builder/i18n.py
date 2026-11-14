STRINGS = {
    "fi": {
        "title": "Livemusiikki Turussa",
        "description": "Kaikki Turun keikat yhdessä paikassa: baarikeikoista konserttisaleihin. Varaa liput ajoissa.",
        "nav_week": "Tällä viikolla",
        "nav_upcoming": "Tulossa",
        "nav_calendar": "Kalenteri",
        "all_venues": "Kaikki paikat",
        "venues_label": "Suodata paikan mukaan",
        "today": "Tänään",
        "tomorrow": "Huomenna",
        "doors": "Ovet",
        "add_cal": "Lisää kalenteriin",
        "start": "Alkaa",
        "empty": "Ei keikkoja valituilla suodattimilla.",
        "empty_week": "Ei keikkoja tällä viikolla. Katso mitä on tulossa.",
        "empty_day": "Ei keikkoja tänä päivänä.",
        "gigs": ["keikka", "keikkaa"],
        "prev": "Edellinen kuukausi",
        "next": "Seuraava kuukausi",
        "updated": "Päivitetty",
        "sold_out": "Loppuunmyyty",
        "other_lang": "English",
        "other_lang_code": "en",
    },
    "en": {
        "title": "Live Music in Turku",
        "description": "Every gig in Turku in one place, from bar shows to concert halls. Book your tickets early.",
        "nav_week": "This week",
        "nav_upcoming": "Coming up",
        "nav_calendar": "Calendar",
        "all_venues": "All venues",
        "venues_label": "Filter by venue",
        "today": "Today",
        "tomorrow": "Tomorrow",
        "doors": "Doors",
        "add_cal": "Add to calendar",
        "start": "Starts",
        "empty": "No gigs match these filters.",
        "empty_week": "No gigs this week. See what's coming up.",
        "empty_day": "No gigs on this day.",
        "gigs": ["gig", "gigs"],
        "prev": "Previous month",
        "next": "Next month",
        "updated": "Updated",
        "sold_out": "Sold out",
        "other_lang": "Suomeksi",
        "other_lang_code": "fi",
    },
}

WEEKDAYS = {
    "fi": ["maanantai", "tiistai", "keskiviikko", "torstai", "perjantai", "lauantai", "sunnuntai"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
WEEKDAYS_SHORT = {
    "fi": ["Ma", "Ti", "Ke", "To", "Pe", "La", "Su"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}
# Genitive ("14. marraskuuta") for dates, nominative ("marraskuu") for headings.
MONTHS = {
    "fi": ["tammikuuta", "helmikuuta", "maaliskuuta", "huhtikuuta", "toukokuuta", "kesäkuuta",
           "heinäkuuta", "elokuuta", "syyskuuta", "lokakuuta", "marraskuuta", "joulukuuta"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}
MONTHS_NOMINATIVE = {
    "fi": ["tammikuu", "helmikuu", "maaliskuu", "huhtikuu", "toukokuu", "kesäkuu",
           "heinäkuu", "elokuu", "syyskuu", "lokakuu", "marraskuu", "joulukuu"],
    "en": MONTHS["en"],
}
MONTHS_SHORT = {
    "fi": ["tammi", "helmi", "maalis", "huhti", "touko", "kesä", "heinä", "elo", "syys", "loka", "marras", "joulu"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}


def format_day(d, lang: str) -> str:
    wd, month = WEEKDAYS[lang][d.weekday()], MONTHS[lang][d.month - 1]
    return f"{wd} {d.day}. {month}" if lang == "fi" else f"{wd} {d.day} {month}"


def format_month(d, lang: str) -> str:
    return f"{MONTHS_NOMINATIVE[lang][d.month - 1].capitalize()} {d.year}"


def format_age(age: int | None, lang: str) -> str | None:
    if age is None:
        return None
    return f"K{age}" if lang == "fi" else f"{age}+"
