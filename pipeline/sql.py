"""Running the SQL transforms in pipeline/transform/ against a DuckDB connection."""
from datetime import date
from pathlib import Path

import duckdb

TRANSFORM_DIR = Path(__file__).parent / "transform"
SEEDS_DIR = Path(__file__).parent / "seeds"


def run_sql(con: duckdb.DuckDBPyConnection, sql_file: Path, today: date) -> None:
    sql = (sql_file.read_text()
           .replace("{{today}}", today.isoformat())
           .replace("{{seeds_dir}}", SEEDS_DIR.resolve().as_posix()))
    con.execute(sql)


def transform(con: duckdb.DuckDBPyConnection, today: date) -> None:
    for sql_file in sorted(TRANSFORM_DIR.glob("*.sql")):
        run_sql(con, sql_file, today)
