from datetime import date

import duckdb

COLUMNS = ["source", "venue", "title", "date", "doors", "start", "age_limit", "url"]


def load(con: duckdb.DuckDBPyConnection, source: str, events: list[dict], today: date) -> None:
    """Append one scrape of one source to staging.events_raw.

    Re-running the same source on the same day replaces that day's rows,
    so the load is idempotent.
    """
    con.execute("CREATE SCHEMA IF NOT EXISTS staging")
    con.execute("""
        CREATE TABLE IF NOT EXISTS staging.events_raw (
            source VARCHAR, venue VARCHAR, title VARCHAR, date DATE,
            doors VARCHAR, start VARCHAR, age_limit INTEGER, url VARCHAR,
            scraped_on DATE
        )
    """)
    con.execute("DELETE FROM staging.events_raw WHERE source = ? AND scraped_on = ?",
                [source, today])
    con.executemany(
        "INSERT INTO staging.events_raw VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [[e[c] for c in COLUMNS] + [today] for e in events],
    )
