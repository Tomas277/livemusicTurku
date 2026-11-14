import os
import sys
from datetime import date

import duckdb

from pipeline import checks, history
from pipeline.extract import apollo, dynamo, fuuga, fuusio, kuka, logomo
from pipeline.load import load
from pipeline.sql import transform

HISTORY_CSV = history.DEFAULT_PATH
SOURCES = {"dynamo": dynamo, "kuka": kuka, "apollo": apollo, "fuusio": fuusio, "fuuga": fuuga, "logomo": logomo}


def main() -> None:
    today = date.today()
    con = duckdb.connect()  # in memory: the committed history CSV is the only state that survives a run
    history.restore(con, HISTORY_CSV)

    failed = []
    # Set LIVEMUSIC_SOURCES=fuuga,kuka to scrape only some sources locally (the rest keep their history).
    only = {n for n in os.environ.get("LIVEMUSIC_SOURCES", "").split(",") if n}
    # LIVEMUSIC_ACCEPT=kuka lets a venue that really shrank its program through the gig-count check once.
    accept = {n for n in os.environ.get("LIVEMUSIC_ACCEPT", "").replace(" ", "").split(",") if n}
    for name, module in SOURCES.items():
        if only and name not in only:
            continue
        try:
            events = module.extract(today)
            problems = checks.check_events(name, events, today,
                                           history.previous_upcoming_count(con, name, today),
                                           accept_drop=name in accept)
            if not problems:
                load(con, name, events, today)
        except Exception as exc:  # one broken source must not stop the others
            failed.append(name)
            print(f"{name}: FAILED - {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        if problems:  # a suspicious scrape is not trusted: the last good one stays on the site
            failed.append(name)
            for problem in problems:
                print(f"{name}: CHECK FAILED - {problem}", file=sys.stderr)
            continue
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
