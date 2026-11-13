from datetime import date
from pathlib import Path

import duckdb

from pipeline.extract import dynamo
from pipeline.load import load

WAREHOUSE = Path("data/warehouse.duckdb")
TRANSFORM_DIR = Path(__file__).parent / "transform"
SOURCES = {"dynamo": dynamo}


def transform(con: duckdb.DuckDBPyConnection, today: date) -> None:
    for sql_file in sorted(TRANSFORM_DIR.glob("*.sql")):
        con.execute(sql_file.read_text().replace("{{today}}", today.isoformat()))


def main() -> None:
    today = date.today()
    WAREHOUSE.parent.mkdir(exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE))
    for name, module in SOURCES.items():
        events = module.extract(today)
        load(con, name, events, today)
        print(f"{name}: loaded {len(events)} events")
    transform(con, today)
    n = con.execute("SELECT count(*) FROM marts.upcoming_events").fetchone()[0]
    print(f"marts.upcoming_events: {n} rows")


if __name__ == "__main__":
    main()
