import sys
from datetime import date
from pathlib import Path

import duckdb

from pipeline.extract import apollo, dynamo, fuusio, kuka
from pipeline.load import load

WAREHOUSE = Path("data/warehouse.duckdb")
TRANSFORM_DIR = Path(__file__).parent / "transform"
SEEDS_DIR = Path(__file__).parent / "seeds"
SOURCES = {"dynamo": dynamo, "kuka": kuka, "apollo": apollo, "fuusio": fuusio}


def transform(con: duckdb.DuckDBPyConnection, today: date) -> None:
    for sql_file in sorted(TRANSFORM_DIR.glob("*.sql")):
        sql = (sql_file.read_text()
               .replace("{{today}}", today.isoformat())
               .replace("{{seeds_dir}}", SEEDS_DIR.resolve().as_posix()))
        con.execute(sql)


def main() -> None:
    today = date.today()
    WAREHOUSE.parent.mkdir(exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE))
    failed = []
    for name, module in SOURCES.items():
        try:
            events = module.extract(today)
        except Exception as exc:  # one broken scraper must not stop the others
            failed.append(name)
            print(f"{name}: FAILED - {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        load(con, name, events, today)
        print(f"{name}: loaded {len(events)} events")
    transform(con, today)
    for venue, n in con.execute(
            "SELECT venue, count(*) FROM marts.upcoming_events GROUP BY venue ORDER BY venue").fetchall():
        print(f"  upcoming {venue}: {n}")
    if failed:
        print(f"FAILED SOURCES: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
