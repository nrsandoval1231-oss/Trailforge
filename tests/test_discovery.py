import http.client
import json
import threading
import time
import xml.etree.ElementTree as ET

import pytest

import athena_procurement_arena.discovery as discovery_module
from athena_procurement_arena.discovery import FEEDS, MAX_RESPONSE, fetch_feed, parse_feed
from athena_procurement_arena.operator import Server, Store

RSS = b"""<rss><channel><item><title>Silver Springs construction</title><link>https://local.microsoft.com/blog/silver-springs/</link><pubDate>Mon, 28 Sep 2026 12:00:00 +0000</pubDate></item><item><title>Off site</title><link>https://evil.example/item</link></item></channel></rss>"""


def test_parse_feed_allowlist_dates_and_bad_xml():
    items, excluded, fetched = parse_feed(RSS, "microsoft-local")
    assert (len(items), excluded, fetched) == (1, 1, 2)
    assert items[0]["source_date"].startswith("2026-09-28T12:00:00")
    with pytest.raises(ValueError, match="DOCTYPE"):
        parse_feed(b"<!DOCTYPE x [<!ENTITY y 'z'>]><rss/>", "microsoft-local")
    with pytest.raises(ValueError, match="UTF-8"):
        parse_feed("<!DOCTYPE rss><rss/>".encode("utf-16"), "microsoft-local")
    for encoding in ("utf-16-le", "utf-16-be"):
        payload = "<!DOCTYPE rss [<!ENTITY x 'expanded'>]><rss><channel><title>&x;</title></channel></rss>".encode(encoding)
        with pytest.raises(ValueError, match="UTF-8"):
            parse_feed(payload, "microsoft-local")
    with pytest.raises(ValueError, match="root"):
        parse_feed(b"<html/>", "microsoft-local")
    with pytest.raises(ET.ParseError):
        parse_feed(b"<rss>", "microsoft-local")
    with pytest.raises(ValueError, match="1 MiB"):
        parse_feed(b" " * (MAX_RESPONSE + 1), "microsoft-local")


def test_atom_offhost_and_bad_url_excluded():
    atom = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>One</title><link href="https://q.com/news/one"/><updated>2026-09-28T12:00:00Z</updated></entry><entry><title>Bad</title><link href="http://q.com/no"/></entry></feed>'
    items, excluded, fetched = parse_feed(atom, "qts-news")
    assert len(items) == 1 and excluded == 1 and fetched == 2


def test_fetch_rejects_nonpublic_dns_and_redirect(monkeypatch):
    monkeypatch.setattr(discovery_module, "_resolve_public_addresses", lambda host, deadline: ())
    with pytest.raises(ValueError, match="public addresses"):
        fetch_feed(FEEDS["microsoft-local"][0], FEEDS["microsoft-local"][1])

    user_agents = []

    class Redirect:
        def __init__(self, *args, **kwargs):
            self.sock = type("Socket", (), {"settimeout": lambda self, value: None})()
            self.headers = None

        def request(self, *args, **kwargs):
            self.headers = kwargs["headers"]
            user_agents.append(self.headers.get("User-Agent"))

        def remaining(self):
            return 1

        def getresponse(self):
            return type("Response", (), {"status": 302})()

        def close(self):
            pass

    monkeypatch.setattr(discovery_module, "_resolve_public_addresses", lambda host, deadline: ("8.8.8.8",))
    monkeypatch.setattr(discovery_module, "PinnedHTTPSConnection", Redirect)
    with pytest.raises(ValueError, match="redirect rejected"):
        fetch_feed(FEEDS["microsoft-local"][0], FEEDS["microsoft-local"][1])
    assert user_agents == ["TrailForge/0.1 (public project research)"]


def test_dns_resolution_obeys_total_deadline(monkeypatch):
    release = threading.Event()

    def stalled_lookup(*args, **kwargs):
        release.wait(2)
        return []

    monkeypatch.setattr(discovery_module.socket, "getaddrinfo", stalled_lookup)
    started = time.monotonic()
    with pytest.raises(TimeoutError, match="DNS resolution"):
        discovery_module._resolve_public_addresses("fixed.example", started + 0.03)
    assert time.monotonic() - started < 0.5
    release.set()
    assert discovery_module._DNS_SLOT.acquire(timeout=1)
    discovery_module._DNS_SLOT.release()


def test_dedupe_failure_retention_restart_and_idempotent_admission(tmp_path):
    store = Store(tmp_path / "operator.sqlite3")
    discovery = store.discovery
    responses = {"microsoft-local": RSS, "qts-news": b"<rss><channel/></rss>"}

    def fetch(url, host):
        source_id = next(k for k, pair in FEEDS.items() if pair[0] == url)
        return responses[source_id]

    first = discovery.check(fetch)
    item = next(c for c in first["candidates"] if c["source_id"] == "microsoft-local")
    seen = item["first_seen"]
    discovery.check(fetch)
    repeated = next(c for c in discovery.listing()["candidates"] if c["id"] == item["id"])
    assert repeated["first_seen"] == seen and repeated["status"] == "PENDING_REVIEW"
    responses["microsoft-local"] = b"<rss>"
    failed = discovery.check(fetch)
    assert next(f for f in failed["feeds"] if f["source_id"] == "microsoft-local")["error"]
    assert any(c["id"] == item["id"] for c in failed["candidates"])
    project, is_repeat = discovery.admit(item["id"], item["title"], "UNKNOWN", "UNKNOWN")
    assert project["gate"]["need"] == "UNKNOWN" and project["gate"]["buyer"] == "UNKNOWN"
    assert project["evidence"][0]["review_status"] == "UNKNOWN"
    same, is_repeat = discovery.admit(item["id"], "ignored", "", "")
    assert is_repeat and same["id"] == project["id"]
    store.close()
    store = Store(tmp_path / "operator.sqlite3")
    assert store.discovery.listing()["candidates"][0]["project_id"] == project["id"]
    assert len(store.listing()) == 1
    store.close()


def test_http_discovery_routes_are_protected_and_allow_no_arbitrary_url(tmp_path):
    store = Store(tmp_path / "operator.sqlite3")
    server = Server(store, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        def request(method, path, payload=None, token=None):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            body = None if payload is None else json.dumps(payload)
            headers = {"Host": server.authority}
            if body is not None:
                headers.update({"Content-Type": "application/json", "Content-Length": str(len(body.encode()))})
            if token:
                headers["X-Operator-Token"] = token
            conn.request(method, path, body=body, headers=headers)
            response = conn.getresponse()
            result = response.status
            response.read()
            conn.close()
            return result

        assert request("GET", "/api/discovery") == 200
        assert request("POST", "/api/discovery/check", {}, "wrong") == 403
        assert request("POST", "/api/discovery/check", {"url": "https://example.com"}, server.token) == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        store.close()
