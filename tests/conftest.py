from pathlib import Path

import duckdb

from pipeline import history

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def empty_con() -> duckdb.DuckDBPyConnection:
    """An in-memory database with an empty history table, as history.restore leaves it on the first run."""
    con = duckdb.connect()
    history.restore(con, Path("does-not-exist.csv"))
    return con
