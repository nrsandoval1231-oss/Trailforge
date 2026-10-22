"""Unreviewed public-web leads: URL normalization and a SQLite store (classification lives in lead_classifier).

Nothing here verifies anything. The classifier only reports which words matched so an operator can see why a
search hit was flagged; every lead starts NEW and stays unreviewed until a human acts on it.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import re
import sqlite3
import threading
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .lead_classifier import CLASSIFIER_VERSION, Classification, classify, deadline_status
from .public_capture import _public_url

__all__ = ["CLASSIFIER_VERSION", "Classification", "KINDS", "LeadStore", "STATUSES", "classify", "lead_id_for",
           "normalize_url"]

KINDS = ("RFP", "PROJECT", "OTHER")
STATUSES = ("NEW", "DISMISSED", "SNOOZED", "CAPTURED")
LEAD_ID = re.compile(r"[0-9a-f]{16}\Z")
MAX_TITLE = 500
MAX_SNIPPET = 2000
MAX_URL = 2000
MAX_SNOOZE_DAYS = 365
_TRACKING = {"gclid", "fbclid", "msclkid", "mc_cid", "mc_eid"}


# ----- URL identity -----
def normalize_url(url: str) -> str:
    """Public http(s) URL with lowercase host, no fragment, no tracking params, no trailing slash."""
    _public_url(url)
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower().rstrip(".")
    if ":" in host:
        host = f"[{host}]"  # bare IPv6 literal
    port = parts.port
    if port and (parts.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
        host = f"{host}:{port}"
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in _TRACKING]
    return urlunsplit((parts.scheme.lower(), host, parts.path.rstrip("/"), urlencode(query), ""))


def lead_id_for(normalized_url: str) -> str:
    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()[:16]


# ----- store -----
def _stamp(now: datetime | None) -> str:
    return (now or datetime.now(UTC)).astimezone(UTC).isoformat(timespec="seconds")


def _today(now: datetime | None) -> date:
    return (now or datetime.now()).astimezone().date()  # the operator's local calendar day


def _like(value: str) -> str:
    return "%" + value.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY, url TEXT NOT NULL, title TEXT NOT NULL, snippet TEXT NOT NULL, source_type TEXT NOT NULL,
  query_ids TEXT NOT NULL, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('NEW','DISMISSED','SNOOZED','CAPTURED')), snooze_until TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('RFP','PROJECT','OTHER')), matched TEXT NOT NULL, score INTEGER NOT NULL,
  capture_id TEXT, capture_path TEXT, capture_sha256 TEXT, captured_at TEXT, original_url TEXT);
CREATE INDEX IF NOT EXISTS leads_status_kind ON leads (status, kind);
CREATE TABLE IF NOT EXISTS search_runs (
  run_id TEXT PRIMARY KEY, query_id TEXT NOT NULL, query_text TEXT NOT NULL, started_at TEXT NOT NULL,
  finished_at TEXT, hit_count INTEGER NOT NULL DEFAULT 0, new_count INTEGER NOT NULL DEFAULT 0, error TEXT);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


class LeadStore:
    """Thread-safe lead + search-run store. One short-lived connection per operation; WAL; parameterized SQL."""

    def __init__(self, path: str | Path, official_hosts=()):
        self.path = Path(path)
        self._lock = threading.RLock()
        self._ready = False
        self._applied: str | None = None  # classifier key last checked against the meta table
        self._official_hosts: tuple[str, ...] = ()
        self.set_official_hosts(official_hosts)

    def set_official_hosts(self, hosts) -> None:
        """Extra hosts (e.g. the discovery catalog's `domains`) that count as official sources when ranking."""
        with self._lock:
            cleaned = {h.strip().lower().strip(".") for h in hosts if isinstance(h, str)}
            # a single label ("org", "com") would make a whole TLD official
            self._official_hosts = tuple(sorted(h for h in cleaned if "." in h and " " not in h and "/" not in h))

    def _classifier_key(self) -> str:
        digest = hashlib.sha256("\n".join(self._official_hosts).encode()).hexdigest()[:8] if self._official_hosts else ""
        return f"{CLASSIFIER_VERSION}:{digest}" if digest else str(CLASSIFIER_VERSION)

    def _classify(self, title: str, snippet: str, url: str) -> Classification:
        return classify(title, snippet, url, self._official_hosts)

    def _reclassify_if_stale(self, conn) -> None:
        """Re-run the classifier over every stored lead when the stored classifier key differs.

        Only kind, matched and score are rewritten (never status, snooze, capture refs or timestamps), in one
        transaction, so a crash leaves the old ranking and the next open simply tries again. Idempotent.
        """
        key = self._classifier_key()
        if self._applied == key:
            return
        try:
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as exc:
            if "readonly" in str(exc).lower().replace(" ", ""):  # read-only database: serve it as it is
                self._applied = key
                return
            raise
        try:
            row = conn.execute("SELECT value FROM meta WHERE key = 'classifier_version'").fetchone()
            if row is None or row["value"] != key:
                for lead in conn.execute("SELECT id, url, title, snippet FROM leads").fetchall():
                    try:
                        found = self._classify(lead["title"], lead["snippet"], lead["url"])
                    except Exception:  # noqa: BLE001 - one odd stored row keeps its old ranking, never blocks the tab
                        continue
                    conn.execute("UPDATE leads SET kind = ?, matched = ?, score = ? WHERE id = ?",
                                 (found.kind, json.dumps(found.matched()), found.score, lead["id"]))
                conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('classifier_version', ?)", (key,))
            conn.execute("COMMIT")
        except sqlite3.OperationalError as exc:
            conn.execute("ROLLBACK")
            if "readonly" not in str(exc).lower().replace(" ", ""):
                raise
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        self._applied = key  # also after a read-only skip, so reads do not retry the re-rank on every call

    @staticmethod
    def _prepare(conn) -> None:
        """WAL + schema + older-database columns. Safe when another store instance opens the same file."""
        for attempt in range(40):
            try:
                # switching the journal mode ignores the busy timeout while another connection is open
                if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() != "wal":
                    conn.execute("PRAGMA journal_mode=WAL")
                conn.executescript(_SCHEMA)
                if "original_url" not in {r["name"] for r in conn.execute("PRAGMA table_info(leads)")}:
                    conn.execute("ALTER TABLE leads ADD COLUMN original_url TEXT")
                return
            except sqlite3.OperationalError as exc:
                message = str(exc).lower()
                if "readonly" in message.replace(" ", ""):  # read-only database: nothing to prepare, reads still work
                    return
                # retry only when another instance holds the lock or added the column first
                if attempt == 39 or not any(m in message for m in ("locked", "busy", "duplicate column")):
                    raise
                time.sleep(0.05)

    @contextlib.contextmanager
    def _connect(self, write: bool = False):
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
            try:
                conn.row_factory = sqlite3.Row
                if not self._ready:
                    self._prepare(conn)
                    self._ready = True
                self._reclassify_if_stale(conn)
                conn.execute("PRAGMA synchronous=NORMAL")
                if write:
                    conn.execute("BEGIN IMMEDIATE")
                try:
                    yield conn
                except BaseException:
                    if write:
                        conn.execute("ROLLBACK")
                    raise
                if write:
                    conn.execute("COMMIT")
            finally:
                conn.close()

    @staticmethod
    def _expire(conn, now: datetime | None) -> None:
        conn.execute("UPDATE leads SET status = CASE WHEN capture_id IS NULL THEN 'NEW' ELSE 'CAPTURED' END, "
                     "snooze_until = NULL WHERE status = 'SNOOZED' AND snooze_until <= ?", (_stamp(now),))

    @staticmethod
    def _lead(row, today) -> dict:
        capture = None
        if row["capture_id"]:
            capture = {"capture_id": row["capture_id"], "path": row["capture_path"],
                       "content_sha256": row["capture_sha256"], "captured_at": row["captured_at"]}
        matched = json.loads(row["matched"])
        lead = {"id": row["id"], "url": row["url"], "original_url": (row["original_url"] if "original_url" in row.keys() else None) or row["url"],
                "host": urlsplit(row["url"]).hostname or "",
                "title": row["title"], "snippet": row["snippet"], "source_type": row["source_type"],
                "query_ids": json.loads(row["query_ids"]), "first_seen": row["first_seen"],
                "last_seen": row["last_seen"], "status": row["status"], "snooze_until": row["snooze_until"],
                "kind": row["kind"], "matched": matched, "score": row["score"],
                "capture": capture}
        # computed per read against today (never stored): how the date quoted in the snippet compares with today
        status = deadline_status(matched.get("deadline_hint"), today)
        if status:
            lead["deadline_status"] = status
        return lead

    def upsert_hit(self, url: str, title: str, snippet: str, source_type: str, query_id: str,
                   now: datetime | None = None) -> tuple[str, bool]:
        """Insert or refresh one search hit. Returns (lead_id, is_new). Never changes an existing status."""
        if len(url.strip()) > MAX_URL:
            raise ValueError("URL is too long")
        normalized = normalize_url(url)
        lead_id = lead_id_for(normalized)
        title, snippet = str(title or "").strip()[:MAX_TITLE], str(snippet or "").strip()[:MAX_SNIPPET]
        stamp = _stamp(now)
        with self._connect(write=True) as conn:
            row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
            if row is None:
                found = self._classify(title, snippet, normalized)
                conn.execute(
                    "INSERT INTO leads (id, url, title, snippet, source_type, query_ids, first_seen, last_seen, status,"
                    " kind, matched, score, original_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?, ?, ?)",
                    (lead_id, normalized, title, snippet, str(source_type or "web")[:40],
                     json.dumps([query_id]), stamp, stamp, found.kind, json.dumps(found.matched()), found.score,
                     url.strip()))
                return lead_id, True
            query_ids = sorted({*json.loads(row["query_ids"]), query_id})
            title, snippet = title or row["title"], snippet or row["snippet"]
            found = self._classify(title, snippet, normalized)
            conn.execute("UPDATE leads SET title = ?, snippet = ?, query_ids = ?, last_seen = ?, kind = ?, "
                         "matched = ?, score = ? WHERE id = ?",
                         (title, snippet, json.dumps(query_ids), stamp, found.kind, json.dumps(found.matched()),
                          found.score, lead_id))
            return lead_id, False

    def get(self, lead_id: str, now: datetime | None = None) -> dict | None:
        if not LEAD_ID.fullmatch(lead_id):
            return None
        with self._connect(write=True) as conn:
            self._expire(conn, now)
            row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return self._lead(row, _today(now)) if row else None

    def leads(self, *, kind: str | None = None, status: str | None = None, text: str | None = None,
             limit: int = 200, now: datetime | None = None) -> list[dict]:
        """Best first: score, then most recently seen."""
        if kind is not None and kind not in KINDS or status is not None and status not in STATUSES:
            raise ValueError("unknown kind or status filter")
        clauses, params = [], []
        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if text and text.strip():
            clauses.append("(lower(title) LIKE ? ESCAPE '\\' OR lower(snippet) LIKE ? ESCAPE '\\' "
                           "OR lower(url) LIKE ? ESCAPE '\\')")
            params.extend([_like(text.strip()[:200])] * 3)
        limit = max(1, min(int(limit), 500))
        sql = "SELECT * FROM leads" + (" WHERE " + " AND ".join(clauses) if clauses else "")
        sql += " ORDER BY score DESC, last_seen DESC, id LIMIT ?"
        with self._connect(write=True) as conn:
            self._expire(conn, now)
            rows = conn.execute(sql, (*params, limit)).fetchall()
        return [self._lead(row, _today(now)) for row in rows]

    def counts(self, now: datetime | None = None) -> dict:
        with self._connect(write=True) as conn:
            self._expire(conn, now)
            rows = conn.execute("SELECT kind, status, COUNT(*) AS n FROM leads GROUP BY kind, status").fetchall()
        matrix = {kind: {status: 0 for status in STATUSES} for kind in KINDS}
        for row in rows:
            matrix[row["kind"]][row["status"]] = row["n"]
        by_status = {status: sum(matrix[kind][status] for kind in KINDS) for status in STATUSES}
        return {"matrix": matrix, "by_status": by_status, "total": sum(by_status.values())}

    def set_status(self, lead_id: str, action: str, days: int | None = None, now: datetime | None = None) -> dict:
        """dismiss | snooze (days) | restore. Raises LookupError for an unknown lead."""
        if action not in {"dismiss", "snooze", "restore"}:
            raise ValueError("action must be dismiss, snooze, or restore")
        until = None
        if action == "snooze":
            if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= MAX_SNOOZE_DAYS:
                raise ValueError(f"snooze days must be an integer 1..{MAX_SNOOZE_DAYS}")
            until = _stamp((now or datetime.now(UTC)) + timedelta(days=days))
        with self._connect(write=True) as conn:
            row = conn.execute("SELECT capture_id FROM leads WHERE id = ?", (lead_id,)).fetchone()
            if row is None:
                raise LookupError("unknown lead")
            status = {"dismiss": "DISMISSED", "snooze": "SNOOZED",
                      "restore": "CAPTURED" if row["capture_id"] else "NEW"}[action]
            conn.execute("UPDATE leads SET status = ?, snooze_until = ? WHERE id = ?", (status, until, lead_id))
        return self.get(lead_id, now)

    def mark_captured(self, lead_id: str, capture_id: str, path: str, sha256: str, captured_at: str) -> None:
        # An operator decision made while the scrape ran (dismiss, snooze) is kept; the capture ref is still saved.
        with self._connect(write=True) as conn:
            cursor = conn.execute(
                "UPDATE leads SET status = CASE WHEN status = 'NEW' THEN 'CAPTURED' ELSE status END, "
                "snooze_until = CASE WHEN status = 'NEW' THEN NULL ELSE snooze_until END, "
                "capture_id = ?, capture_path = ?, capture_sha256 = ?, captured_at = ? "
                "WHERE id = ? AND capture_id IS NULL",
                (capture_id, path, sha256, captured_at, lead_id))
            if cursor.rowcount != 1:
                raise LookupError("unknown or already captured lead")

    # search runs
    def start_run(self, run_id: str, query_id: str, query_text: str, now: datetime | None = None) -> None:
        with self._connect(write=True) as conn:
            conn.execute("INSERT INTO search_runs (run_id, query_id, query_text, started_at) VALUES (?, ?, ?, ?)",
                         (run_id, query_id, query_text, _stamp(now)))

    def finish_run(self, run_id: str, hit_count: int, new_count: int, error: str | None,
                   now: datetime | None = None) -> None:
        with self._connect(write=True) as conn:
            conn.execute("UPDATE search_runs SET finished_at = ?, hit_count = ?, new_count = ?, error = ? "
                         "WHERE run_id = ?", (_stamp(now), hit_count, new_count, error, run_id))

    def last_run(self) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT MAX(finished_at) AS finished, COUNT(*) AS n FROM search_runs "
                               "WHERE finished_at IS NOT NULL").fetchone()
        return {"finished_at": row["finished"], "queries": row["n"]} if row["finished"] else None

    def runs(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM search_runs ORDER BY started_at DESC, run_id DESC LIMIT ?",
                                (max(1, min(int(limit), 200)),)).fetchall()
        return [dict(row) for row in rows]
