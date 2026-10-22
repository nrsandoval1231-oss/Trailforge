"""Operator-triggered lead search and capture for the Find tab.

Searches and scrapes run in background threads so no HTTP request (or the workbench lock) waits on Firecrawl. Only
the Firecrawl calls the operator explicitly starts leave this machine; results are stored as unreviewed leads.
"""
from __future__ import annotations

import copy
import json
import re
import secrets
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from . import firecrawl_discovery
from .leads import LeadStore, normalize_url
from .opportunity_workspace import REQUIREMENTS, SCHEMA
from .public_capture import _public_url, load_capture

MAX_QUERY_IDS = 13        # one click never exceeds the shipped catalog
MAX_SEARCHES = 14         # catalog queries (one search per configured domain) plus one custom query
MAX_RESULTS = 10          # results per search
CUSTOM_QUERY_MAX = 200
MAX_CAPTURES = 3          # concurrent background scrapes
DISPLAY_CHARS = 20000     # captured text returned to the browser; the file keeps everything
CUSTOM_SOURCES = ("web", "news")
_SLUG = re.compile(r"[^A-Za-z0-9._-]+")


class Busy(RuntimeError):
    """A run or capture is already in progress (HTTP 409)."""


def _now() -> datetime:
    return datetime.now(UTC)


def _describe(exc: BaseException) -> str:
    text = " ".join(str(exc).split())[:300] or exc.__class__.__name__
    if "exit code" in text:
        text += " (check that the Firecrawl CLI is signed in: run `firecrawl --status`, or `firecrawl login`)"
    return text


class FindService:
    def __init__(self, root: Path, safe: Callable[[Path], Path] = lambda path: path.resolve()):
        self.root = Path(root)
        self._safe = safe
        self.store = LeadStore(self._safe(self.root / "leads.sqlite3"))
        self.catalog: dict[str, dict] = {}
        self.catalog_error: str | None = None
        self._lock = threading.RLock()
        self._run: dict | None = None
        self._thread: threading.Thread | None = None
        self._captures: dict[str, dict] = {}
        self._capture_threads: list[threading.Thread] = []

    # ----- catalog -----
    def set_catalog(self, path: Path | None) -> None:
        self.catalog, self.catalog_error = {}, None
        if path is None:
            return
        try:
            self.catalog = firecrawl_discovery.load_catalog(path)
        except (OSError, ValueError) as exc:
            self.catalog_error = f"Discovery catalog could not be loaded: {_describe(exc)}"

    def catalog_view(self) -> list[dict]:
        return [{"id": key, "query": entry["query"], "domains": list(entry.get("domains", [])),
                 "sources": list(entry.get("sources", ["web"])),
                 "searches": max(1, len(entry.get("domains", [])))} for key, entry in self.catalog.items()]

    # ----- search runs -----
    def _plan(self, query_ids, custom, limit) -> list[dict]:
        if not isinstance(query_ids, list) or any(not isinstance(item, str) for item in query_ids):
            raise ValueError("query_ids must be a list of catalog query ids")
        if len(set(query_ids)) != len(query_ids) or len(query_ids) > MAX_QUERY_IDS:
            raise ValueError(f"select each catalog query at most once (maximum {MAX_QUERY_IDS})")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS:
            raise ValueError(f"limit must be an integer 1..{MAX_RESULTS}")
        plan = []
        for query_id in query_ids:
            entry = self.catalog.get(query_id)
            if entry is None:
                raise ValueError(f"unknown catalog query id: {query_id[:60]}")
            plan.append({"query_id": query_id, "label": query_id, "query": entry["query"],
                         "limit": max(1, min(int(entry.get("limit", MAX_RESULTS)), limit)),
                         "sources": tuple(entry.get("sources", ["web"])),
                         "categories": tuple(entry.get("categories", [])),
                         "domains": tuple(entry.get("domains", []))})
        if custom is not None:
            if not isinstance(custom, str) or not custom.strip() or len(custom.strip()) > CUSTOM_QUERY_MAX \
                    or any(ord(char) < 32 for char in custom):
                raise ValueError(f"custom query must be 1..{CUSTOM_QUERY_MAX} characters of plain text")
            text = custom.strip()
            if text.startswith("-"):  # would be read as a Firecrawl CLI option
                raise ValueError("custom query must not start with '-'")
            plan.append({"query_id": f"custom: {text[:80]}", "label": "custom", "query": text, "limit": limit,
                         "sources": CUSTOM_SOURCES, "categories": (), "domains": ()})
        if not plan:
            raise ValueError("choose at least one catalog query or enter a custom query")
        if sum(max(1, len(item["domains"])) for item in plan) > MAX_SEARCHES:
            raise ValueError(f"one run is limited to {MAX_SEARCHES} searches")
        return plan

    def start_run(self, query_ids, custom=None, limit: int = MAX_RESULTS) -> dict:
        jobs = self._jobs(self._plan(query_ids, custom, limit))
        with self._lock:
            if self._run and self._run["state"] == "running":
                raise Busy("A search run is already in progress.")
            run_id = _now().strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)
            self._run = {"run_id": run_id, "state": "running", "started_at": _now().isoformat(timespec="seconds"),
                         "finished_at": None, "total": len(jobs), "done": 0, "current": None, "new_leads": 0,
                         "seen_hits": 0, "searches": len(jobs),
                         "items": [], "errors": []}
            self._thread = threading.Thread(target=self._execute, args=(run_id, jobs), daemon=True,
                                            name="trailforge-find-run")
            self._thread.start()
            return copy.deepcopy(self._run)

    def _update(self, **changes) -> None:
        with self._lock:
            self._run.update(changes)

    @staticmethod
    def _jobs(plan: list[dict]) -> list[dict]:
        """One job per Firecrawl search, so a failing domain never discards hits from domains that succeeded."""
        return [{**item, "domains": (domain,) if domain else (),
                 "name": f"{item['label']} ({domain})" if domain else item["label"]}
                for item in plan for domain in (item["domains"] or ("",))]

    def _execute(self, run_id: str, jobs: list[dict]) -> None:
        try:
            directory = self._safe(self.root / "acquisition" / "searches")
            stamp = run_id.split("-")[0]
            for index, item in enumerate(jobs, start=1):
                self._update(current=item["query_id"] if item["label"] == "custom" else item["name"])
                row_id = f"{run_id}-{index}"
                self.store.start_run(row_id, item["query_id"], item["query"])
                hits = new = 0
                error = fatal = None
                try:
                    slug = _SLUG.sub("-", item["label"]).strip("-._")[:40] or "query"
                    result = firecrawl_discovery.search(
                        item["query"], search_id=f"{slug}-{index}-{stamp}-{secrets.token_hex(2)}", output_dir=directory,
                        limit=item["limit"], sources=item["sources"], categories=item["categories"],
                        domains=item["domains"])
                    for recorded in result["queries"]:
                        saved = json.loads(Path(recorded["path"]).read_text(encoding="utf-8"))
                        for hit in saved["hits"]:
                            try:
                                _, is_new = self.store.upsert_hit(
                                    hit["url"], hit.get("title", ""), hit.get("description", ""),
                                    hit.get("source_type", "web"), item["query_id"])
                            except ValueError:
                                continue  # not a public http(s) URL
                            hits += 1
                            new += is_new
                except Exception as exc:  # one failed search must never abort the rest of the run
                    error = _describe(exc)
                    if isinstance(exc, RuntimeError) and ("not installed" in error or "safely resolve" in error):
                        fatal = error
                self.store.finish_run(row_id, hits, new, error)
                with self._lock:
                    self._run["done"] += 1
                    self._run["new_leads"] += new
                    self._run["seen_hits"] += hits
                    self._run["items"].append({"query": item["name"], "hits": hits, "new": new, "error": error})
                    if error:
                        self._run["errors"].append({"query": item["name"], "error": error})
                if fatal:  # no point repeating a missing CLI for every remaining query
                    break
        except Exception as exc:  # e.g. a store failure: record it, but never leave the run stuck in "running"
            with self._lock:
                self._run["errors"].append({"query": "run", "error": _describe(exc)})
        finally:
            self._update(state="finished", current=None, finished_at=_now().isoformat(timespec="seconds"))

    def join(self, timeout: float = 10) -> None:
        thread = self._thread
        if thread:
            thread.join(timeout)
        for worker in list(self._capture_threads):
            worker.join(timeout)

    def status(self) -> dict:
        with self._lock:
            run = copy.deepcopy(self._run) or {"state": "idle"}
            captures = copy.deepcopy(self._captures)
        return {"run": run, "captures": captures, "counts": self.store.counts(), "last_run": self.store.last_run()}

    # ----- capture -----
    def start_capture(self, lead_id: str, captured_by: str) -> dict:
        lead = self.store.get(lead_id)
        if lead is None:
            raise LookupError("unknown lead")
        if lead["capture"]:
            raise Busy("This lead is already captured.")
        if not isinstance(captured_by, str) or not captured_by.strip() or len(captured_by) > 120:
            raise ValueError("reviewer name is required (1..120 characters)")
        _public_url(lead["original_url"])
        with self._lock:
            if self._captures.get(lead_id, {}).get("state") == "running":
                raise Busy("A capture for this lead is already running.")
            if sum(1 for item in self._captures.values() if item["state"] == "running") >= MAX_CAPTURES:
                raise Busy(f"At most {MAX_CAPTURES} captures can run at once.")
            self._captures[lead_id] = {"state": "running", "error": None}
            worker = threading.Thread(target=self._capture, args=(lead, captured_by.strip()), daemon=True,
                                      name="trailforge-find-capture")
            self._capture_threads = [t for t in self._capture_threads if t.is_alive()] + [worker]
            worker.start()
            return dict(self._captures[lead_id])

    def _capture(self, lead: dict, captured_by: str) -> None:
        capture_id = f"lead-{lead['id']}-{_now().strftime('%Y%m%dT%H%M%SZ')}"
        try:
            directory = self._safe(self.root / "acquisition" / "captures")
            capture, path, _ = firecrawl_discovery.scrape(
                lead["original_url"], capture_id=capture_id, captured_by=captured_by, output_dir=directory,
                source_type=lead["source_type"] or "web", query=", ".join(lead["query_ids"]), max_age_ms=0)
            relative = Path(path).resolve().relative_to(self.root.resolve()).as_posix()
            self.store.mark_captured(lead["id"], capture.capture_id, relative, capture.content_sha256,
                                     capture.captured_at.isoformat())
            outcome = None
        except Exception as exc:  # reported to the operator, never raised into the thread
            outcome = _describe(exc)
        with self._lock:
            if outcome:
                self._captures[lead["id"]] = {"state": "failed", "error": outcome}
            else:
                self._captures.pop(lead["id"], None)

    def _capture_file(self, lead_id: str) -> tuple[dict, Path]:
        lead = self.store.get(lead_id)
        if lead is None:
            raise LookupError("unknown lead")
        if not lead["capture"]:
            raise LookupError("this lead has not been captured")
        base = self.root / "acquisition" / "captures"
        path = self._safe(self.root / lead["capture"]["path"])
        if path.parent != self._safe(base) or not path.is_file():
            raise ValueError("retained capture is missing or outside the capture directory")
        return lead, path

    def capture_text(self, lead_id: str) -> dict:
        lead, path = self._capture_file(lead_id)
        capture = load_capture(path)  # re-verifies the content and capture hashes
        if capture.content_sha256 != lead["capture"]["content_sha256"]:
            raise ValueError("retained capture does not match the hash recorded for this lead")
        text = capture.content
        return {"lead_id": lead_id, "capture_id": capture.capture_id, "source_url": capture.source_url,
                "captured_at": capture.captured_at.isoformat(), "captured_by": capture.captured_by,
                "content_sha256": capture.content_sha256, "total_chars": len(text),
                "truncated": len(text) > DISPLAY_CHARS, "text": text[:DISPLAY_CHARS],
                "notice": "Captured text is unreviewed public-web content, not verified."}

    def opportunity_template(self, lead_id: str) -> dict:
        """Skeleton for `trailforge-opportunity import`; no fact is filled in.

        The search-result title is unreviewed web text, so it is kept out of `title` and appears only under the
        ignored `_lead.search_title` key (the importer reads fields by name and ignores unknown keys).
        """
        lead, path = self._capture_file(lead_id)
        return {
            "_instructions": [
                "Skeleton only. Nothing here is verified or filled in from the capture.",
                "title is null: copy it from the capture, with an exact quote. _lead.search_title is unreviewed.",
                "Set kind to PRE_RFP_PROJECT or ACTIVE_RFP (ACTIVE_RFP also needs cited published_at and deadline).",
                "Every known title, identity fact, date and requirement needs an exact quote from the capture:",
                "add it under field_evidence / requirement_quotes as {\"capture_file\": <path>, \"quote\": <text>}.",
                "Leave unsupported values null. Fill reviewed_by and reviewed_at (with timezone) yourself.",
                "Then: trailforge-opportunity import --workspace DIR --input THIS_FILE",
            ],
            "_lead": {"lead_id": lead["id"], "url": lead["url"], "heuristic_kind": lead["kind"],
                      "search_title": lead["title"] or None,
                      "note": "heuristic label and title come from search text and are unreviewed"},
            "schema_version": SCHEMA,
            "opportunity_id": f"lead-{lead['id']}",
            "kind": None,
            "title": None,
            "identity": {"organization": None, "project": None, "location": None},
            "reviewed_by": None,
            "reviewed_at": None,
            "sources": [{"capture_file": str(path)}],
            "field_evidence": {},
            "requirement_quotes": {},
            "requirements": {name: None for name in REQUIREMENTS},
            "documents": [],
            "notes": f"Lead from public web search (heuristic, unreviewed): {normalize_url(lead['url'])}",
        }
