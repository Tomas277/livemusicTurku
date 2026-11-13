STRINGS = {
    "fi": {
        "title": "Livemusiikki Turussa",
        "tagline": "Kaikki keikat Turussa yhdessä paikassa",
        "all": "Kaikki",
        "today": "Tänään",
        "weekend": "Viikonloppu",
        "venue": "Paikka",
        "all_venues": "Kaikki paikat",
        "doors": "Ovet",
        "start": "Alkaa",
        "tickets": "Lisätiedot",
        "empty": "Ei keikkoja valituilla suodattimilla.",
        "updated": "Päivitetty",
        "other_lang": "English",
        "other_lang_code": "en",
    },
    "en": {
        "title": "Live Music in Turku",
        "tagline": "Every gig in Turku in one place",
        "all": "All",
        "today": "Today",
        "weekend": "Weekend",
        "venue": "Venue",
        "all_venues": "All venues",
        "doors": "Doors",
        "start": "Starts",
        "tickets": "Details",
        "empty": "No gigs match these filters.",
        "updated": "Updated",
        "other_lang": "Suomeksi",
        "other_lang_code": "fi",
    },
}

WEEKDAYS = {
    "fi": ["maanantai", "tiistai", "keskiviikko", "torstai", "perjantai", "lauantai", "sunnuntai"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
MONTHS = {
    "fi": ["tammikuuta", "helmikuuta", "maaliskuuta", "huhtikuuta", "toukokuuta", "kesäkuuta",
           "heinäkuuta", "elokuuta", "syyskuuta", "lokakuuta", "marraskuuta", "joulukuuta"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}


def format_day(d, lang: str) -> str:
    wd, month = WEEKDAYS[lang][d.weekday()], MONTHS[lang][d.month - 1]
    return f"{wd} {d.day}. {month}" if lang == "fi" else f"{wd} {d.day} {month}"


def format_age(age: int | None, lang: str) -> str | None:
    if age is None:
        return None
    return f"K{age}" if lang == "fi" else f"{age}+"
