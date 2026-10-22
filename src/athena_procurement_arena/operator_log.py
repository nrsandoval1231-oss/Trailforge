"""Append-only, hash-chained operator log: evidence review, buying chain, activity (docs/UI_VISION.md Phases 2-3).

Imports stay immutable. Operator judgement is recorded as events that never edit
history; a correction is a new event that supersedes an earlier one.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from athena_arena.contracts import canonical_hash

KINDS = ("claim_review", "conflict_resolution", "buying_chain", "activity", "source_note")
DECISIONS = ("REVIEWED", "REJECTED")
ENTRY_KINDS = ("CONVERSATION", "OUTCOME")
OUTCOMES = ("QUALIFIED", "DISQUALIFIED", "WON", "LOST", "UNRESOLVED")
DIRECT_BUYER_ROLES = ("OWNER", "OPERATOR", "EPC", "EPCM", "GC", "ELECTRICAL_CONTRACTOR")
FUEL_ROLES = ("FUEL_PROVIDER",)
ROLES = (*DIRECT_BUYER_ROLES, *FUEL_ROLES, "OTHER")
ACCESS = ("PUBLIC", "CONFIDENTIAL")
GENESIS = "0" * 64
MAX_TEXT = 4000


class OperatorLogError(ValueError):
    pass


def _text(payload: dict, key: str, *, required: bool = True, limit: int = MAX_TEXT) -> str | None:
    value = payload.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise OperatorLogError(f"{key} is required")
        return None
    if not isinstance(value, str) or len(value) > limit:
        raise OperatorLogError(f"{key} must be text up to {limit} characters")
    return value.strip()


def _choice(payload: dict, key: str, options: tuple[str, ...]) -> str:
    value = _text(payload, key)
    if value not in options:
        raise OperatorLogError(f"{key} must be one of {', '.join(options)}")
    return value


def _when(payload: dict, key: str, now: datetime, *, required: bool) -> str | None:
    value = _text(payload, key, required=required, limit=64)
    if value is None:
        return None
    try:
        moment = datetime.fromisoformat(value)
    except ValueError as exc:
        raise OperatorLogError(f"{key} must be an ISO timestamp") from exc
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise OperatorLogError(f"{key} must be timezone-aware")
    if moment > now:
        raise OperatorLogError(f"{key} cannot be in the future")
    return moment.isoformat()


class OperatorLog:
    """JSONL file; each event commits to the previous event's hash."""

    def __init__(self, path: Path, projects: dict[str, dict[str, Any]]):
        self.path = Path(path)
        self.projects = projects  # project_id -> loaded mining project (sources, requirements)
        self.lock = threading.RLock()
        self.events: list[dict[str, Any]] = []
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        previous = GENESIS
        for number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            event = json.loads(line)
            body = {k: v for k, v in event.items() if k != "event_hash"}
            if event.get("event_id") != number or event.get("prev_hash") != previous \
                    or event.get("event_hash") != canonical_hash(body):
                raise OperatorLogError(f"operator log tampered or corrupt at event {number}")
            previous = event["event_hash"]
            self.events.append(event)

    # ----- validation -----
    def _project(self, project_id: Any) -> dict:
        if not isinstance(project_id, str) or project_id not in self.projects:
            raise OperatorLogError("unknown project")
        return self.projects[project_id]

    def _requirement(self, project: dict, requirement_id: Any) -> dict:
        for req in project["requirements"]:
            if req["requirement_id"] == requirement_id:
                return req
        raise OperatorLogError("unknown requirement for this project")

    @staticmethod
    def _claim(req: dict, field: str) -> dict | None:
        group, _, name = field.partition(".")
        return req.get(group, {}).get(name) if name else req.get(field)

    def _claim_hash(self, event: dict) -> str | None:
        """Hash of the claim as currently imported, or None if it no longer exists."""
        project = self.projects.get(event["project_id"])
        req = next((r for r in project["requirements"] if r["requirement_id"] == event["requirement_id"]), None) \
            if project else None
        claim = self._claim(req, event["payload"]["field"]) if req else None
        return canonical_hash(claim) if claim is not None else None

    def _live(self, project_id: str, kind: str) -> list[dict]:
        replaced = {e["supersedes"] for e in self.events if e.get("supersedes")}
        return [e for e in self.events
                if e["project_id"] == project_id and e["kind"] == kind and e["event_id"] not in replaced]

    def _validate(self, kind: str, project_id: str, requirement_id: str | None,
                  payload: dict, now: datetime) -> dict[str, Any]:
        project = self._project(project_id)
        needs_req = kind in ("claim_review", "conflict_resolution", "activity")
        if needs_req:
            req = self._requirement(project, requirement_id)
        elif requirement_id is not None:
            req = self._requirement(project, requirement_id)
        if kind == "claim_review":
            field = _text(payload, "field", limit=120)
            known = {"phase", "use_case"} | {f"{g}.{n}" for g in ("demand", "delivery", "procurement") for n in req[g]}
            if field not in known:
                raise OperatorLogError("field is not a claim on this requirement")
            return {"field": field, "decision": _choice(payload, "decision", DECISIONS),
                    "note": _text(payload, "note", required=False),
                    "claim_hash": canonical_hash(self._claim(req, field))}
        if kind == "conflict_resolution":
            field = _text(payload, "field", limit=120)
            claim = self._claim(req, field)
            if not claim or claim.get("basis") != "CONFLICT":
                raise OperatorLogError("field is not an unresolved conflict")
            sources = {e["source"] for alt in claim["alternatives"] for e in alt["evidence"]}
            source = _text(payload, "chosen_source", limit=120)
            if source not in sources:
                raise OperatorLogError("chosen_source must be a source cited by a competing claim")
            return {"field": field, "chosen_source": source, "note": _text(payload, "note"),
                    "claim_hash": canonical_hash(claim)}
        if kind == "buying_chain":
            role = _choice(payload, "role", ROLES)
            if role in FUEL_ROLES and not self._fuel_gate_open(project_id):
                raise OperatorLogError("fuel gate: record a direct buyer (owner, EPC/EPCM, GC or electrical "
                                       "contractor) and a logged conversation before fuel providers")
            source = _text(payload, "evidence_source", limit=120)
            if source not in project["sources"] and not any(
                    e["event_id"] == _int(source) for e in self._live(project_id, "source_note")):
                raise OperatorLogError("evidence_source must be a project source or a source_note event id")
            return {"organization": _text(payload, "organization", limit=200),
                    "person": _text(payload, "person", required=False, limit=200), "role": role,
                    "evidence_quote": _text(payload, "evidence_quote"), "evidence_source": source}
        if kind == "activity":
            entry = _choice(payload, "entry", ENTRY_KINDS)
            out = {"entry": entry, "occurred_at": _when(payload, "occurred_at", now, required=True),
                   "summary": _text(payload, "summary"), "outcome": None,
                   "counterparty": _text(payload, "counterparty", required=False, limit=200)}
            if entry == "OUTCOME":
                out["outcome"] = _choice(payload, "outcome", OUTCOMES)
            return out
        # source_note
        url = _text(payload, "url", limit=1000)
        if not url.startswith(("https://", "http://")):
            raise OperatorLogError("url must be http(s)")
        excerpt = _text(payload, "excerpt")
        return {"url": url, "title": _text(payload, "title", limit=300), "excerpt": excerpt,
                "excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest(),
                "access": _choice(payload, "access", ACCESS),
                "published_at": _when(payload, "published_at", now, required=False)}

    def _fuel_gate_open(self, project_id: str) -> bool:
        has_buyer = any(e["payload"]["role"] in DIRECT_BUYER_ROLES for e in self._live(project_id, "buying_chain"))
        talked = any(e["payload"]["entry"] == "CONVERSATION" for e in self._live(project_id, "activity"))
        return has_buyer and talked

    # ----- writes -----
    def append(self, *, kind: str, project_id: str, reviewer: str, payload: dict,
               requirement_id: str | None = None, supersedes: int | None = None,
               now: datetime | None = None) -> dict[str, Any]:
        if kind not in KINDS:
            raise OperatorLogError("unknown event kind")
        if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 120:
            raise OperatorLogError("reviewer name is required")
        if not isinstance(payload, dict):
            raise OperatorLogError("payload must be an object")
        now = now or datetime.now(UTC)
        with self.lock:
            clean = self._validate(kind, project_id, requirement_id, payload, now)
            if supersedes is not None:
                target = next((e for e in self.events if e["event_id"] == supersedes), None)
                if target is None or target["project_id"] != project_id or target["kind"] != kind:
                    raise OperatorLogError("supersedes must name an earlier event of the same kind and project")
                if any(e.get("supersedes") == supersedes for e in self.events):
                    raise OperatorLogError("event was already superseded; edit the latest version")
            body = {"event_id": len(self.events) + 1, "kind": kind, "project_id": project_id,
                    "requirement_id": requirement_id, "recorded_at": now.isoformat(),
                    "reviewer": reviewer.strip(), "payload": clean, "supersedes": supersedes,
                    "prev_hash": self.events[-1]["event_hash"] if self.events else GENESIS}
            event = {**body, "event_hash": canonical_hash(body)}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self.events.append(event)
            return event

    # ----- reads -----
    def view(self) -> dict[str, Any]:
        """Per-project events with superseded/stale flags. Stale: the imported claim changed after review."""
        replaced = {e["supersedes"] for e in self.events if e.get("supersedes")}
        out: dict[str, dict[str, list]] = {}
        for event in self.events:
            bucket = out.setdefault(event["project_id"], {kind: [] for kind in KINDS})
            stale = event["kind"] in ("claim_review", "conflict_resolution") \
                and event["payload"]["claim_hash"] != self._claim_hash(event)
            bucket[event["kind"]].append({**event, "superseded": event["event_id"] in replaced, "stale": stale})
        return {"events": len(self.events), "head": self.events[-1]["event_hash"] if self.events else GENESIS,
                "projects": out}


def _int(value: str) -> int:
    return int(value) if value.isdigit() else -1
