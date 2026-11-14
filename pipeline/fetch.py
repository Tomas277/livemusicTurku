import time
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


client = httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30)
RETRY_DELAYS = (1, 2)  # seconds to wait before the 2nd and 3rd attempt


MAX_RETRY_AFTER = 30   # never sleep longer than this because a server asked


def _wait_time(resp: httpx.Response, delay: float) -> float:
    """The backoff delay, or the server's own numeric Retry-After (capped) when it sent one."""
    value = resp.headers.get("Retry-After", "")
    return min(int(value), MAX_RETRY_AFTER) if value.isdigit() else delay


def request(method: str, url: str, **kwargs) -> httpx.Response:
    """One HTTP request. Network errors, 5xx and 429 answers are retried twice; other 4xx fail at once."""
    for delay in (*RETRY_DELAYS, None):
        try:
            resp = client.request(method, url, **kwargs)
            if not (resp.status_code >= 500 or resp.status_code == 429) or delay is None:
                resp.raise_for_status()
                return resp
            wait = _wait_time(resp, delay)
        except httpx.TransportError:
            if delay is None:
                raise
            wait = delay
        time.sleep(wait)


def get(url: str, **kwargs) -> httpx.Response:
    return request("GET", url, **kwargs)


def post(url: str, **kwargs) -> httpx.Response:
    return request("POST", url, **kwargs)


def fetch_raw(source: str, url: str, today: date, name: str = "page") -> str:
    """Download a page and keep a raw copy."""
    text = get(url).text
    save_raw(source, today, name, text)
    return text
