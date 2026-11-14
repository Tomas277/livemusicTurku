from datetime import date

import duckdb

from pipeline.event import COLUMNS, OPTIONAL, SQL_TYPES


def load(con: duckdb.DuckDBPyConnection, source: str, events: list[dict], today: date) -> None:
    """Append one scrape of one source to staging.events_raw.

    Re-running the same source on the same day replaces that day's rows,
    so the load is idempotent.
    """
    con.execute("CREATE SCHEMA IF NOT EXISTS staging")
    columns = {**SQL_TYPES, "scraped_on": "DATE"}
    con.execute(f"CREATE TABLE IF NOT EXISTS staging.events_raw ({', '.join(f'{k} {v}' for k, v in columns.items())})")
    for name, sql_type in columns.items():  # a table made by an older version of the pipeline may lack newer columns
        con.execute(f"ALTER TABLE staging.events_raw ADD COLUMN IF NOT EXISTS {name} {sql_type}")
    con.execute("DELETE FROM staging.events_raw WHERE source = ? AND scraped_on = ?",
                [source, today])
    cols = ", ".join([*COLUMNS, "scraped_on"])
    con.executemany(
        f"INSERT INTO staging.events_raw ({cols}) VALUES ({', '.join('?' * (len(COLUMNS) + 1))})",
        [[e.get(c) if c in OPTIONAL else e[c] for c in COLUMNS] + [today] for e in events],
    )
