"""Bounded, on-demand discovery from two fixed official owner news feeds."""

from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import socket
import ssl
import threading
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from queue import Empty, Queue
from urllib.parse import urlsplit

FEEDS = {
    "microsoft-local": ("https://local.microsoft.com/feed/", "local.microsoft.com"),
    "qts-news": ("https://q.com/news/feed/", "q.com"),
}
MAX_RESPONSE = 1024 * 1024
MAX_ITEMS = 50
FETCH_DEADLINE_SECONDS = 10
_DNS_SLOT = threading.BoundedSemaphore(1)


def utc_now():
    return datetime.now(UTC).isoformat(timespec="seconds")


def _resolve_public_addresses(host: str, deadline: float):
    remaining = deadline - time.monotonic()
    if remaining <= 0 or not _DNS_SLOT.acquire(timeout=remaining):
        raise TimeoutError("feed DNS resolution exceeded 10-second source deadline")
    result = Queue(maxsize=1)

    def resolve():
        try:
            try:
                result.put((socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM), None))
            except Exception as exc:
                result.put((None, exc))
        finally:
            _DNS_SLOT.release()

    threading.Thread(target=resolve, name="trailforge-feed-dns", daemon=True).start()
    try:
        records, error = result.get(timeout=max(0, deadline - time.monotonic()))
    except Empty as exc:
        raise TimeoutError("feed DNS resolution exceeded 10-second source deadline") from exc
    if time.monotonic() >= deadline:
        raise TimeoutError("feed DNS resolution exceeded 10-second source deadline")
    if error:
        raise OSError(f"feed DNS resolution failed: {error}") from error
    addresses = tuple(dict.fromkeys(row[4][0] for row in records))
    if not addresses or not all(ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("feed host did not resolve exclusively to public addresses")
    return addresses


def _child_text(entry, name):
    child = next((node for node in entry if node.tag.rsplit("}", 1)[-1] == name), None)
    return " ".join("".join(child.itertext()).split()) if child is not None else ""


def parse_feed(raw: bytes, source_id: str):
    if len(raw) > MAX_RESPONSE:
        raise ValueError("response exceeded 1 MiB limit")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("feed must use UTF-8 XML") from exc
    if "\x00" in text:
        raise ValueError("feed must use UTF-8 XML")
    upper = text.upper()
    if "<!DOCTYPE" in upper or "<!ENTITY" in upper:
        raise ValueError("DOCTYPE and ENTITY are forbidden")
    root = ET.fromstring(text)
    if root.tag.rsplit("}", 1)[-1] not in {"rss", "feed"}:
        raise ValueError("XML root must be RSS or Atom feed")
    entries = root.findall(".//item")
    if not entries:
        entries = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "entry"]
    items, excluded = [], 0
    for entry in entries[:MAX_ITEMS]:
        title = _child_text(entry, "title")
        link = _child_text(entry, "link")
        if not link:
            link_node = next((node for node in entry if node.tag.rsplit("}", 1)[-1] == "link"), None)
            link = link_node.attrib.get("href", "") if link_node is not None else ""
        parsed = urlsplit(link)
        allowed = urlsplit(FEEDS[source_id][0])[1]
        if parsed.scheme != "https" or parsed.hostname != allowed or parsed.username or parsed.password:
            excluded += 1
            continue
        date = _child_text(entry, "pubDate") or _child_text(entry, "published") or _child_text(entry, "updated")
        if date:
            try:
                parsed_date = parsedate_to_datetime(date)
                date = parsed_date.isoformat() if parsed_date.tzinfo else "UNKNOWN"
            except (TypeError, ValueError, OverflowError):
                try:
                    parsed_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                    date = parsed_date.isoformat() if parsed_date.tzinfo else "UNKNOWN"
                except ValueError:
                    date = "UNKNOWN"
        else:
            date = "UNKNOWN"
        if title and link:
            items.append({"title": title[:1000], "url": link, "source_date": date})
    return items, excluded, len(entries)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, addresses, deadline: float):
        super().__init__(host, timeout=max(0.001, deadline - time.monotonic()), context=ssl.create_default_context())
        self.addresses = addresses
        self.deadline = deadline

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("feed fetch exceeded 10-second source deadline")
        return remaining

    def connect(self):
        last_error = None
        for address in self.addresses:
            raw = None
            try:
                raw = socket.create_connection((address, self.port), self.remaining(), self.source_address)
                raw.settimeout(self.remaining())
                self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
                self.sock.settimeout(self.remaining())
                return
            except Exception as exc:
                if raw is not None:
                    raw.close()
                last_error = exc
        raise OSError("could not connect to checked public feed addresses") from last_error


def fetch_feed(url: str, host: str) -> bytes:
    deadline = time.monotonic() + FETCH_DEADLINE_SECONDS
    addresses = _resolve_public_addresses(host, deadline)
    if not addresses:
        raise ValueError("feed host did not resolve exclusively to public addresses")
    parsed = urlsplit(url)
    connection = PinnedHTTPSConnection(host, addresses, deadline)
    try:
        connection.request(
            "GET",
            parsed.path or "/",
            headers={
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
                "User-Agent": "TrailForge/0.1 (public project research)",
            },
        )
        connection.sock.settimeout(connection.remaining())
        response = connection.getresponse()
        if 300 <= response.status < 400:
            raise ValueError("redirect rejected")
        if response.status != 200:
            raise ValueError(f"HTTP status {response.status}")
        content_type = response.headers.get_content_type()
        if content_type not in {"application/rss+xml", "application/atom+xml", "application/xml", "text/xml"}:
            raise ValueError("response was not XML")
        data = bytearray()
        while len(data) <= MAX_RESPONSE:
            connection.sock.settimeout(connection.remaining())
            chunk = response.read1(min(64 * 1024, MAX_RESPONSE + 1 - len(data)))
            if not chunk:
                connection.remaining()
                return bytes(data)
            data.extend(chunk)
        raise ValueError("response exceeded 1 MiB limit")
    finally:
        connection.close()


class Discovery:
    def __init__(self, store):
        self.store = store

    def listing(self, search=""):
        needle = f"%{search.strip()}%"
        with self.store.lock:
            rows = self.store.db.execute(
                "SELECT candidate_id,source_id,title,url,source_date,first_seen,status,snapshot_hash,project_id "
                "FROM discovery_candidates WHERE title LIKE ? OR url LIKE ? ORDER BY first_seen DESC",
                (needle, needle),
            ).fetchall()
            feeds = self.store.db.execute(
                "SELECT source_id,checked_at,last_success,error,fetched_count,eligible_count,excluded_count, "
                "(SELECT count(*) FROM discovery_candidates c WHERE c.source_id=discovery_checks.source_id AND c.status='DISMISSED') "
                "FROM discovery_checks"
            ).fetchall()
        candidates = [dict(zip(("id", "source_id", "title", "url", "source_date", "first_seen", "status", "snapshot_hash", "project_id"), row, strict=True)) for row in rows]
        return {"candidates": candidates, "feeds": [dict(zip(("source_id", "checked_at", "last_success", "error", "fetched_count", "eligible_count", "excluded_count", "dismissed_count"), row, strict=True)) for row in feeds]}

    def check(self, fetch=fetch_feed):
        results = []
        for source_id, (url, host) in FEEDS.items():
            checked = utc_now()
            try:
                items, excluded, fetched = parse_feed(fetch(url, host), source_id)
                with self.store.lock:
                    self.store.db.execute("BEGIN IMMEDIATE")
                    try:
                        for item in items:
                            snapshot = hashlib.sha256((item["title"] + "\0" + item["url"]).encode()).hexdigest()
                            self.store.db.execute(
                                "INSERT INTO discovery_candidates VALUES (?,?,?,?,?,?,?,?,NULL) "
                                "ON CONFLICT(url) DO UPDATE SET title=excluded.title,source_date=excluded.source_date,snapshot_hash=excluded.snapshot_hash",
                                (hashlib.sha256(item["url"].encode()).hexdigest(), source_id, item["title"], item["url"], item["source_date"], checked, snapshot, "PENDING_REVIEW"),
                            )
                        self.store.db.execute(
                            "INSERT INTO discovery_checks VALUES (?,?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET checked_at=excluded.checked_at,last_success=excluded.last_success,error=excluded.error,fetched_count=excluded.fetched_count,eligible_count=excluded.eligible_count,excluded_count=excluded.excluded_count",
                            (source_id, checked, checked, "", fetched, len(items), excluded),
                        )
                        self.store.db.execute("COMMIT")
                    except Exception:
                        self.store.db.execute("ROLLBACK")
                        raise
                results.append({"source_id": source_id, "ok": True, "fetched_count": fetched, "eligible_count": len(items), "excluded_count": excluded})
            except Exception as exc:  # retain older candidates and publish source failure
                with self.store.lock:
                    self.store.db.execute(
                        "INSERT INTO discovery_checks VALUES (?,?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET checked_at=excluded.checked_at,error=excluded.error",
                        (source_id, checked, "", str(exc)[:500], 0, 0, 0),
                    )
                results.append({"source_id": source_id, "ok": False, "error": str(exc)[:500]})
        return {"results": results, **self.listing()}

    def admit(self, candidate_id: str, name: str, location: str, phase: str):
        from .operator import blank, validate_doc

        with self.store.lock:
            self.store.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.store.db.execute("SELECT url,title,project_id FROM discovery_candidates WHERE candidate_id=?", (candidate_id,)).fetchone()
                if row is None:
                    raise KeyError("candidate not found")
                if row[2]:
                    project = self.store.get(row[2])
                    self.store.db.execute("COMMIT")
                    return project, True
                excerpt = "Official owner feed candidate admitted; power need, supply, timing, and buyer remain UNKNOWN."
                evidence = {"id": hashlib.sha256((candidate_id + "project").encode()).hexdigest()[:32], "claim": "project", "value": "UNKNOWN", "source_url": row[0], "excerpt": excerpt, "source_date": "", "observed_at": utc_now(), "reviewer": "", "review_status": "UNKNOWN", "sha256": hashlib.sha256(excerpt.encode()).hexdigest(), "supersedes": []}
                doc = blank(name, location, phase)
                doc["evidence"].append(evidence)
                validate_doc(doc)
                payload = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                self.store.db.execute("INSERT INTO projects VALUES (?,?,?)", (doc["id"], doc["version"], payload))
                project = self.store.get(doc["id"])
                self.store.db.execute("UPDATE discovery_candidates SET status='ADMITTED',project_id=? WHERE candidate_id=?", (project["id"], candidate_id))
                self.store.db.execute("COMMIT")
                return project, False
            except Exception:
                self.store.db.execute("ROLLBACK")
                raise

    def set_status(self, candidate_id: str, status: str):
        if status not in {"PENDING_REVIEW", "DISMISSED"}:
            raise ValueError("invalid discovery status")
        with self.store.lock:
            cur = self.store.db.execute("UPDATE discovery_candidates SET status=? WHERE candidate_id=? AND project_id IS NULL", (status, candidate_id))
            if cur.rowcount != 1:
                raise ValueError("candidate not found or already admitted")
