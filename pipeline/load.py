from dataclasses import astuple
from datetime import date

import duckdb

from pipeline.event import COLUMNS, SQL_TYPES, Event


def load(con: duckdb.DuckDBPyConnection, source: str, events: list[Event], today: date) -> None:
    """Append one scrape of one source to staging.events_raw.

    Re-running the same source on the same day replaces that day's rows,
    so the load is idempotent.
    """
    con.execute("CREATE SCHEMA IF NOT EXISTS staging")
    columns = {**SQL_TYPES, "scraped_on": "DATE"}
    con.execute(f"CREATE TABLE IF NOT EXISTS staging.events_raw ({', '.join(f'{k} {v}' for k, v in columns.items())})")
    cols = ", ".join([*COLUMNS, "scraped_on"])
    con.begin()  # delete and insert succeed or fail together, so a half-written scrape never counts as today's
    try:
        con.execute("DELETE FROM staging.events_raw WHERE source = ? AND scraped_on = ?", [source, today])
        con.executemany(
            f"INSERT INTO staging.events_raw ({cols}) VALUES ({', '.join('?' * (len(COLUMNS) + 1))})",
            [[*astuple(e), today] for e in events],
        )
    except BaseException:
        con.rollback()
        raise
    con.commit()
