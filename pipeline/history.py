"""The event history lives in a CSV that is committed to git (the free 'warehouse').

Each run restores it into DuckDB, merges today's scrape with SQL, and saves it back.
"""
from datetime import date
from pathlib import Path

import duckdb

COLUMNS = {
    "source": "VARCHAR", "venue": "VARCHAR", "title": "VARCHAR", "date": "DATE",
    "doors": "VARCHAR", "start": "VARCHAR", "age_limit": "INTEGER", "url": "VARCHAR",
    "access": "VARCHAR", "availability": "VARCHAR", "first_seen": "DATE", "last_seen": "DATE",
}


def _sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def restore(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    """Load history.events_history from the CSV, or start empty on the very first run."""
    con.execute("CREATE SCHEMA IF NOT EXISTS history")
    if path.exists():
        # Older history files were written before some columns existed; fill those with NULL.
        present = path.read_text(encoding="utf-8").split("\n", 1)[0].strip().split(",")
        cols = ", ".join(f"'{k}': '{COLUMNS[k]}'" for k in present)
        select = ", ".join(k if k in present else f"NULL::{v} AS {k}" for k, v in COLUMNS.items())
        con.execute("CREATE OR REPLACE TABLE history.events_history AS "
                    f"SELECT {select} FROM read_csv('{_sql_path(path)}', header = true, columns = {{{cols}}})")
    else:
        cols = ", ".join(f"{k} {v}" for k, v in COLUMNS.items())
        con.execute(f"CREATE OR REPLACE TABLE history.events_history ({cols})")


def save(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    """Write the history back, in a fixed order so git diffs only show real changes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    con.execute("COPY (SELECT * FROM history.events_history "
                "ORDER BY date, source, title, first_seen) "
                f"TO '{_sql_path(path)}' (HEADER, DELIMITER ',')")


def previous_upcoming_count(con: duckdb.DuckDBPyConnection, source: str, today: date) -> int:
    """How many upcoming gigs the source's most recent successful scrape had."""
    return con.execute("""
        SELECT count(*) FROM history.events_history h
        WHERE h.source = ? AND h.date >= ?
          AND h.last_seen = (SELECT max(last_seen) FROM history.events_history WHERE source = ?)
    """, [source, today, source]).fetchone()[0]
