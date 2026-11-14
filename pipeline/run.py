import os
import sys
from datetime import date
from pathlib import Path

import duckdb

from pipeline import checks, history
from pipeline.extract import apollo, dynamo, fuuga, fuusio, kuka, logomo
from pipeline.load import load

WAREHOUSE = Path("data/warehouse.duckdb")
# The committed history. Set LIVEMUSIC_HISTORY to experiment locally without touching it.
HISTORY_CSV = Path(os.environ.get("LIVEMUSIC_HISTORY", "data/warehouse/events_history.csv"))
TRANSFORM_DIR = Path(__file__).parent / "transform"
SEEDS_DIR = Path(__file__).parent / "seeds"
SOURCES = {"dynamo": dynamo, "kuka": kuka, "apollo": apollo, "fuusio": fuusio, "fuuga": fuuga, "logomo": logomo}


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
    history.restore(con, HISTORY_CSV)

    failed = []
    # Set LIVEMUSIC_SOURCES=fuuga,kuka to scrape only some sources locally (the rest keep their history).
    only = {n for n in os.environ.get("LIVEMUSIC_SOURCES", "").split(",") if n}
    for name, module in SOURCES.items():
        if only and name not in only:
            continue
        try:
            events = module.extract(today)
        except Exception as exc:  # one broken scraper must not stop the others
            failed.append(name)
            print(f"{name}: FAILED - {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        problems = checks.check_events(name, events, today,
                                       history.previous_upcoming_count(con, name, today))
        if problems:  # a suspicious scrape is not trusted: the last good one stays on the site
            failed.append(name)
            for problem in problems:
                print(f"{name}: CHECK FAILED - {problem}", file=sys.stderr)
            continue
        load(con, name, events, today)
        print(f"{name}: loaded {len(events)} events")

    transform(con, today)
    history.save(con, HISTORY_CSV)
    for venue, n in con.execute(
            "SELECT venue, count(*) FROM marts.upcoming_events GROUP BY venue ORDER BY venue").fetchall():
        print(f"  on the site: {venue} {n}")
    if failed:
        print(f"FAILED SOURCES: {', '.join(failed)} (their last good data is kept)", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
