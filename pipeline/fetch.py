from datetime import date
from pathlib import Path

import httpx

USER_AGENT = "livemusicTurku/0.1 (hobby event aggregator)"
RAW_DIR = Path("raw")


def fetch_raw(source: str, url: str, today: date, name: str = "page") -> str:
    """Download a page and keep a copy under raw/<source>/<date>/<name>.html."""
    resp = httpx.get(url, headers={"User-Agent": USER_AGENT},
                     follow_redirects=True, timeout=30)
    resp.raise_for_status()
    path = RAW_DIR / source / today.isoformat() / f"{name}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(resp.text, encoding="utf-8")
    return resp.text
