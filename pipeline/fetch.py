from datetime import date
from pathlib import Path

import httpx

USER_AGENT = "livemusicTurku/0.1 (hobby event aggregator)"
HEADERS = {"User-Agent": USER_AGENT}
RAW_DIR = Path("raw")


def save_raw(source: str, today: date, name: str, text: str) -> None:
    """Keep a copy under raw/<source>/<date>/<name>.html so parsers can be re-run later."""
    path = RAW_DIR / source / today.isoformat() / f"{name}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fetch_raw(source: str, url: str, today: date, name: str = "page") -> str:
    """Download a page and keep a raw copy."""
    resp = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
    resp.raise_for_status()
    save_raw(source, today, name, resp.text)
    return resp.text
