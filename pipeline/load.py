from datetime import date

import duckdb

COLUMNS = ["source", "venue", "title", "date", "doors", "start", "age_limit", "url", "access", "availability"]
# Optional fields: not every venue publishes whether entry is free or how many tickets are left.
OPTIONAL = {"access", "availability"}


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
    for col in OPTIONAL:  # tables created by older versions of the pipeline lack these
        con.execute(f"ALTER TABLE staging.events_raw ADD COLUMN IF NOT EXISTS {col} VARCHAR")
    con.execute("DELETE FROM staging.events_raw WHERE source = ? AND scraped_on = ?",
                [source, today])
    cols = ", ".join(COLUMNS + ["scraped_on"])
    con.executemany(
        f"INSERT INTO staging.events_raw ({cols}) VALUES ({', '.join('?' * (len(COLUMNS) + 1))})",
        [[e.get(c) if c in OPTIONAL else e[c] for c in COLUMNS] + [today] for e in events],
    )
