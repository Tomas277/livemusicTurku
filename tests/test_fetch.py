from datetime import date

import httpx
import pytest

from conftest import fixture
from pipeline import fetch
from pipeline.extract import logomo


def use_answers(monkeypatch, answers):
    """Make fetch talk to a fake site that gives the listed answers (a status code or an exception) in order."""
    calls = []

    def handler(request):
        calls.append(request)
        answer = answers[min(len(calls), len(answers)) - 1]
        if isinstance(answer, Exception):
            raise answer
        return httpx.Response(answer, text="ok")

    monkeypatch.setattr(fetch, "client", httpx.Client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(fetch, "RETRY_DELAYS", (0, 0))
    return calls


def test_a_server_error_is_retried_until_it_works(monkeypatch):
    calls = use_answers(monkeypatch, [503, httpx.ConnectError("down"), 200])
    assert fetch.get("https://x/").text == "ok"
    assert len(calls) == 3


def test_three_server_errors_give_up(monkeypatch):
    calls = use_answers(monkeypatch, [503])
    with pytest.raises(httpx.HTTPStatusError):
        fetch.post("https://x/", json={})
    assert len(calls) == 3


def test_a_client_error_is_not_retried(monkeypatch):
    calls = use_answers(monkeypatch, [404])
    with pytest.raises(httpx.HTTPStatusError):
        fetch.get("https://x/")
    assert len(calls) == 1


def test_logomo_skips_one_failing_page(monkeypatch, capsys):
    sitemap = fixture("logomo_sitemap.xml")
    urls = logomo.event_urls(sitemap)
    page = fixture("logomo_event.html")

    def fake_fetch_raw(source, url, today, name="page"):
        if url == urls[0]:
            raise httpx.ConnectError("down")
        return page

    monkeypatch.setattr(logomo, "get", lambda url: httpx.Response(200, text=sitemap))
    monkeypatch.setattr(logomo, "fetch_raw", fake_fetch_raw)
    monkeypatch.setattr(logomo.time, "sleep", lambda s: None)
    events = logomo.extract(date(2026, 11, 14))
    assert len(events) == len(urls) - 1
    assert urls[0] in capsys.readouterr().err
