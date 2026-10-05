"""Evidence-bound local opportunity records and static operator response workspace."""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from athena_arena.contracts import canonical_hash

from .foundation import ClaimBasis, EvidenceEvent
from .opportunity_brief import BUYER_TYPES, EXCLUDED_BUYER_TYPES, build_brief
from .public_capture import _public_url, load_capture
from .rfp_intake import screen_aura_rental_candidate

SCHEMA = "trailforge-opportunity-input-v1"
REQUIREMENTS = ("required_kw", "program_mw", "voltage", "duty", "redundancy", "runtime", "fuel",
                "emissions", "mobilization", "duration", "deadline", "prebid", "bonding", "insurance",
                "certifications", "forms", "submission", "clarifications", "scope")
COLLECTIONS = ("certifications", "forms", "direct_buyer_orgs", "roles")
_ID = re.compile(r"[^a-zA-Z0-9._-]+")


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _stamp(value: str | datetime, field: str) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include timezone")
    return parsed


def _date_or_stamp(value: str | datetime, field: str) -> tuple[str, datetime]:
    if isinstance(value, str):
        try:
            parsed_date = date.fromisoformat(value)
            return parsed_date.isoformat(), datetime.combine(parsed_date, time.min, UTC)
        except ValueError:
            pass
    parsed = _stamp(value, field)
    return parsed.isoformat(), parsed


def _safe_url(value: str) -> str:
    return _public_url(value)


def _copy_immutable(source: Path, target: Path, expected_sha256: str | None = None) -> str:
    if not source.is_file():
        raise FileNotFoundError(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if expected_sha256 and digest != expected_sha256.lower():
        raise ValueError(f"original file hash mismatch: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError(f"immutable workspace path collision: {target}")
    else:
        shutil.copyfile(source, target)
    return digest


def _capture_reference(name: str, captures: dict[str, dict[str, Any]], base: Path,
                       workspace: Path) -> dict[str, Any]:
    source_path = (base / name).resolve()
    capture = load_capture(source_path)
    stored = workspace / "captures" / f"{capture.capture_hash}.capture.json"
    _copy_immutable(source_path, stored)
    metadata_name = (source_path.name[:-len(".capture.json")] + ".acquisition.json"
                    if source_path.name.endswith(".capture.json")
                    else source_path.stem + ".acquisition.json")
    metadata_path = source_path.with_name(metadata_name)
    metadata: dict[str, Any] = {}
    if metadata_path.exists():
        metadata = _json(metadata_path)
        if (metadata.get("capture_sha256") != capture.content_sha256
                or metadata.get("capture_id") not in (None, capture.capture_id)
                or metadata.get("source_url") not in (None, capture.source_url)):
            raise ValueError(f"capture metadata hash does not match {source_path}")
    descriptor = {"capture_file": str(stored.relative_to(workspace)), "capture_id": capture.capture_id,
                  "capture_hash": capture.capture_hash, "source_url": capture.source_url,
                  "canonical_url": capture.source_url,
                  "content_sha256": capture.content_sha256, "captured_at": capture.captured_at.isoformat(),
                  "provider": capture.provider, "provider_job_id": capture.provider_job_id,
                  "query": metadata.get("query"), "source_type": metadata.get("source_type"),
                  "title": metadata.get("title"), "scraped_at": metadata.get("scraped_at"),
                  "acquisition": metadata,
                  "cache_state": metadata.get("cache_state"), "cached_at": metadata.get("cached_at"),
                  "freshness_requested_max_age_ms": metadata.get("freshness_requested_max_age_ms"),
                  "completed_at": metadata.get("completed_at"),
                  "retrieved_at": metadata.get("retrieved_at"),
                  "domain": metadata.get("domain", urlparse(capture.source_url).hostname)}
    existing = captures.get(capture.capture_hash)
    if existing and existing["capture_hash"] != descriptor["capture_hash"]:
        raise ValueError("conflicting captures share one content digest")
    if existing:
        for key, value in existing.items():
            if descriptor.get(key) is None and key not in {"acquisition", "cache_state", "cached_at",
                    "freshness_requested_max_age_ms", "completed_at", "retrieved_at"}:
                descriptor[key] = value
    captures[capture.capture_hash] = descriptor
    return descriptor


def _exact_evidence(field: str, value: Any, evidence: dict[str, Any], captures: dict[str, dict[str, Any]],
                    base: Path, workspace: Path) -> dict[str, Any]:
    if not isinstance(evidence, dict) or not isinstance(evidence.get("quote"), str):
        raise ValueError(f"known field {field} requires an exact source quote")
    source_name = evidence.get("capture_file")
    if not isinstance(source_name, str):
        raise ValueError(f"known field {field} requires capture_file")
    descriptor = _capture_reference(source_name, captures, base, workspace)
    capture = load_capture(workspace / descriptor["capture_file"])
    quote = evidence["quote"]
    if not quote.strip() or quote not in capture.content:
        raise ValueError(f"source quote for {field} is not an exact span in capture")
    return {"capture_sha256": capture.content_sha256, "capture_hash": capture.capture_hash,
            "quote": quote, "source_url": capture.source_url, "canonical_url": capture.source_url}


def _identity_key(kind: str, identity: dict[str, Any]) -> str | None:
    def known_value(field: str) -> str | None:
        value = " ".join(str(identity.get(field) or "").casefold().split())
        return value if value and value != "unknown" else None

    organization = known_value("organization")
    if kind == "ACTIVE_RFP":
        official_id = known_value("official_id")
        return canonical_hash({"kind": kind, "organization": organization, "official_id": official_id}) if organization and official_id else None
    project = known_value("project")
    location = known_value("location")
    return canonical_hash({"kind": kind, "organization": organization, "project": project, "location": location}) if organization and project and location else None


def _record_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    """Retain every imported fact and citation without recursive merge history."""
    return {key: value for key, value in record.items() if key not in {"record_hash", "evidence_history"}}


def _citation_candidate(claim: dict[str, Any] | None) -> dict[str, Any] | None:
    if not claim:
        return None
    return {key: claim.get(key) for key in ("value", "quote", "capture_hash", "capture_sha256", "source_url", "canonical_url",
                                             "title", "source_type", "acquisition", "documents")}


def _fresh_capture_time(record: dict[str, Any], claim: dict[str, Any] | None, now: datetime) -> datetime | None:
    if not claim:
        return None
    source = record.get("sources", {}).get(claim.get("capture_hash"), {})
    try:
        requested = source["freshness_requested_max_age_ms"]
        if isinstance(requested, bool) or not isinstance(requested, int) or requested != 0:
            return None
        acquisition = source["acquisition"]
        if (acquisition.get("capture_id") != source.get("capture_id")
                or acquisition.get("source_url") != source.get("source_url")
                or acquisition.get("capture_sha256") != source.get("content_sha256")):
            return None
        cache_state = str(source["cache_state"]).casefold()
        if cache_state not in {"miss", "bypass", "refreshed"}:
            return None
        acquired = _stamp(source.get("completed_at") or source["retrieved_at"], "retrieved_at")
        if not now - timedelta(hours=24) <= acquired <= now + timedelta(minutes=5):
            return None
        cached_at = source.get("cached_at")
        if cached_at is not None:
            cached = _stamp(cached_at, "cached_at")
            if not now - timedelta(hours=24) <= cached <= now + timedelta(minutes=5):
                return None
        return acquired
    except (KeyError, TypeError, ValueError):
        return None


def _fresh_capture(record: dict[str, Any], claim: dict[str, Any] | None, now: datetime) -> bool:
    return _fresh_capture_time(record, claim, now) is not None


def _qualification(record: dict[str, Any], now: datetime) -> dict[str, Any]:
    requirements = record["requirements"]
    if record["kind"] != "ACTIVE_RFP":
        return {"status": "NOT_SCREENED", "reason_codes": ["NOT_AN_ACTIVE_RFP"]}
    deadline = record.get("deadline")
    try:
        deadline_at = _stamp(deadline["value"], "deadline") if deadline else None
    except (KeyError, TypeError, ValueError):
        deadline_at = None
    if record.get("requirement_conflicts"):
        return {"status": "NEEDS_REVIEW", "reason_codes": ["CONFLICTING_REQUIREMENTS_REQUIRE_HUMAN_REVIEW"],
                "deadline_current": False, "capture_fresh": "UNKNOWN", "lifecycle_status": "UNKNOWN",
                "requirement_conflict_fields": sorted(record["requirement_conflicts"])}
    if deadline_at is not None and deadline_at <= now:
        return {"status": "NOT_CURRENT", "reason_codes": ["EXPLICIT_DEADLINE_EXPIRED"],
                "deadline_current": False, "capture_fresh": "UNKNOWN",
                "amendments_status": "UNKNOWN", "lifecycle_status": "EXPIRED"}
    if record.get("date_conflicts"):
        fields = sorted(record["date_conflicts"])
        return {"status": "NEEDS_REVIEW", "reason_codes": ["CONFLICTING_SOURCE_DATES_REQUIRE_HUMAN_REVIEW"],
                "deadline_current": False, "capture_fresh": "UNKNOWN", "lifecycle_status": "UNKNOWN",
                "date_conflict_fields": fields}
    if deadline_at is None:
        return {"status": "NEEDS_REVIEW", "reason_codes": ["EXPLICIT_DEADLINE_REQUIRED"],
                "deadline_current": False, "capture_fresh": "UNKNOWN", "lifecycle_status": "UNKNOWN"}
    # Freshness must be evidenced by the exact capture that states the deadline.
    source = record["sources"].get(deadline.get("capture_hash"), {})
    is_fresh = _fresh_capture(record, deadline, now)
    if not is_fresh:
        return {"status": "NEEDS_REVIEW", "reason_codes": ["EXPLICIT_CURRENT_DEADLINE_AND_FRESH_CAPTURE_REQUIRED"],
                "lifecycle_status": "UNKNOWN"}
    claims = {key: value for key, value in requirements.items() if value is not None}
    _, event_date = _date_or_stamp((record.get("published_at") or {}).get("value", record["reviewed_at"]), "published_at")
    spans = tuple(item["quote"] for item in record["requirement_quotes"].values())
    evidence = EvidenceEvent(evidence_id=f"workspace-{record['opportunity_id']}",
        source_id=source.get("source_url", "https://invalid.example/unknown"), event_date=event_date,
        document_date=event_date, verified_available_at=now, observed_at=now, claims=claims,
        claim_basis=ClaimBasis.REPORTED, source_version=canonical_hash(record["sources"]),
        lineage_family=f"opportunity:{record['opportunity_id']}", authority="REVIEWED_MANUAL_SOURCE",
        source_spans=spans, permission_scope="PUBLIC")
    screen = screen_aura_rental_candidate((evidence,))
    status = {"REJECTED": "NOT_FIT", "NEEDS_REVIEW": "NEEDS_REVIEW",
              "QUALIFIED": "POTENTIAL_FIT_PENDING_HUMAN_REVIEW"}[str(screen.status)]
    return {"status": status, "screen_status": str(screen.status), "reason_codes": list(screen.reason_codes),
            "required_kw": screen.required_kw, "deadline_current": True,
            "capture_fresh": "FRESH_ACQUISITION_MAX_AGE_ZERO" if is_fresh else "UNKNOWN",
            "amendments_status": "UNKNOWN", "lifecycle_status": "OPEN_AS_OF_PUBLIC_SOURCE"}


def import_opportunity(input_file: str | Path, workspace_dir: str | Path, *, now: datetime | None = None) -> dict[str, Any]:
    """Import reviewed evidence, preserve captures, and refuse unproven field values."""
    input_path = Path(input_file).resolve()
    item = _json(input_path)
    if item.get("schema_version") != SCHEMA:
        raise ValueError(f"input schema_version must be {SCHEMA}")
    kind = item.get("kind")
    if kind not in {"PRE_RFP_PROJECT", "ACTIVE_RFP"}:
        raise ValueError("kind must be PRE_RFP_PROJECT or ACTIVE_RFP")
    if not item.get("opportunity_id") or not item.get("reviewed_by"):
        raise ValueError("opportunity_id and reviewed_by are required")
    buyer_type = str(item["buyer_type"]).upper() if item.get("buyer_type") else None
    if buyer_type is not None and buyer_type not in BUYER_TYPES:
        raise ValueError(f"buyer_type must be one of {sorted(BUYER_TYPES)}")
    if item.get("procurement_route") is not None and not isinstance(item["procurement_route"], str):
        raise ValueError("procurement_route must be a string")
    reviewed_at = _stamp(item["reviewed_at"], "reviewed_at")
    assessment_time = now or datetime.now(UTC)
    workspace = Path(workspace_dir).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    manifest_path = workspace / "workspace.json"
    manifest = _json(manifest_path) if manifest_path.exists() else {"schema_version": "trailforge-operator-workspace-v1", "opportunities": []}
    for existing_record in manifest.get("opportunities", []):
        if existing_record.get("record_hash") != canonical_hash(
            {key: value for key, value in existing_record.items() if key != "record_hash"}
        ):
            raise ValueError(f"existing opportunity record hash mismatch: {existing_record.get('opportunity_id')}")
    captures: dict[str, dict[str, Any]] = {}
    sources: dict[str, Any] = {}
    source_inputs = item.get("sources")
    if not isinstance(source_inputs, list) or not source_inputs:
        raise ValueError("at least one source capture is required")
    for source in source_inputs:
        if not isinstance(source, dict) or not isinstance(source.get("capture_file"), str):
            raise ValueError("each source requires capture_file")
        descriptor = _capture_reference(source["capture_file"], captures, input_path.parent, workspace)
        for key in ("query", "source_type", "title", "scraped_at"):
            # Intake may add descriptive labels; acquisition facts come only from the bound sidecar.
            if source.get(key) is not None:
                descriptor[key] = descriptor.get(key) or source[key]
        captures[descriptor["capture_hash"]] = descriptor
        sources[descriptor["capture_hash"]] = descriptor
    evidence_raw = item.get("field_evidence", {})
    field_evidence: dict[str, Any] = {}
    known_fields = {"title": item.get("title")}
    identity = item.get("identity", {})
    if not isinstance(identity, dict):
        raise ValueError("identity must be an object")
    for key, value in identity.items():
        known_fields[f"identity.{key}"] = value
    for key, value in known_fields.items():
        if value is not None:
            field_evidence[key] = _exact_evidence(key, value, evidence_raw.get(key), captures, input_path.parent, workspace)
    for key in ("direct_buyer_orgs", "roles", "procurement_route"):
        value = item.get(key, [])
        if value:
            field_evidence[key] = _exact_evidence(key, value, evidence_raw.get(key), captures, input_path.parent, workspace)
    requirements = item.get("requirements", {})
    if not isinstance(requirements, dict):
        raise ValueError("requirements must be an object")
    requirements = {key: requirements.get(key) for key in REQUIREMENTS}
    requirement_quotes: dict[str, Any] = {}
    quote_raw = item.get("requirement_quotes", {})
    for key, value in requirements.items():
        if value is not None:
            requirement_quotes[key] = _exact_evidence(key, value, quote_raw.get(key), captures, input_path.parent, workspace)
    dates: dict[str, Any] = {}
    for key in ("published_at", "deadline", "earliest_signal"):
        claim = item.get(key)
        if claim is not None:
            value, _ = _date_or_stamp(claim["value"], key)
            dates[key] = {"value": value,
                          **_exact_evidence(key, claim["value"], claim, captures, input_path.parent, workspace)}
    if kind == "ACTIVE_RFP" and (not dates.get("deadline") or not dates.get("published_at")):
        raise ValueError("ACTIVE_RFP requires explicitly cited published_at and deadline")
    documents = []
    for document in item.get("documents", []):
        url = _safe_url(document["url"])
        copied = {"title": document.get("title"), "url": url, "source_type": document.get("source_type", "document"),
                  "capture_sha256": None, "capture_file": None, "original_file": None, "original_sha256": None}
        if document.get("capture_file"):
            desc = _capture_reference(document["capture_file"], captures, input_path.parent, workspace)
            copied.update(capture_sha256=desc["content_sha256"], capture_file=desc["capture_file"])
        if document.get("original_file"):
            original = (input_path.parent / document["original_file"]).resolve()
            digest = hashlib.sha256(original.read_bytes()).hexdigest()
            if document.get("sha256") and digest != document["sha256"]:
                raise ValueError("document original sha256 mismatch")
            target = workspace / "documents" / f"{digest}{original.suffix.lower()}"
            _copy_immutable(original, target, digest)
            copied.update(original_file=str(target.relative_to(workspace)), original_sha256=digest)
        documents.append(copied)
    # Include captures cited by fields and requirements even when the capture was not listed first.
    sources = dict(captures)
    first_seen = min((source["captured_at"] for source in sources.values()), default=None)
    record = {"schema_version": "trailforge-opportunity-v1", "opportunity_id": str(item["opportunity_id"]),
        "project_id": _identity_key(kind, identity), "canonical_project_id": _identity_key(kind, identity),
        "opportunity_type": kind, "first_seen_at": first_seen,
        "status": kind, "vertical": item.get("vertical") or item.get("signal_family"),
        "kind": kind, "title": item.get("title"), "identity": identity, "identity_key": _identity_key(kind, identity),
        "identity_resolution": "RESOLVED" if _identity_key(kind, identity) else "UNKNOWN",
        "reviewed_by": item["reviewed_by"], "reviewed_at": reviewed_at.isoformat(), "sources": sources,
        "field_evidence": field_evidence, "published_at": dates.get("published_at"), "deadline": dates.get("deadline"),
        "earliest_signal": dates.get("earliest_signal"), "requirements": requirements,
        "requirement_quotes": requirement_quotes, "signal_family": item.get("signal_family"),
        "power_gap_hypothesis": item.get("power_gap_hypothesis"),
        "direct_buyer_orgs": item.get("direct_buyer_orgs", []), "roles": item.get("roles", []),
        "procurement_route": item.get("procurement_route"), "buyer_type": buyer_type,
        "next_action": item.get("next_action") or "HUMAN_REVIEW_SOURCE_AND_REQUIREMENTS",
        "documents": documents, "notes": item.get("notes", ""),
        "qualification": None, "qualification_assessed_at": assessment_time.isoformat(),
        "response_workspace": {"draft_file": f"drafts/{_ID.sub('-', str(item['opportunity_id']))}.json"}}
    record["qualification"] = _qualification(record, assessment_time)
    record["status"] = record["qualification"].get("lifecycle_status", kind)
    record["missing_information"] = [field for field, value in requirements.items()
                                     if (value is None or value == [])
                                     and not (field == "deadline" and record["deadline"] is not None)]
    record["record_hash"] = canonical_hash(record)
    draft_path = workspace / record["response_workspace"]["draft_file"]
    if not draft_path.exists():
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(json.dumps({"schema_version": "trailforge-rfp-draft-v1",
            "opportunity_id": record["opportunity_id"], "outline": ["Buyer and project context",
            "Requirements and citations", "Compliance matrix", "Unanswered questions",
            "Commercial and technical assumptions"], "draft_placeholders": {"executive_summary": "",
            "technical_response": "", "commercial_response": ""}, "completion_state": "NOT_STARTED"},
            sort_keys=True, indent=2) + "\n", encoding="utf-8")
    for old in manifest["opportunities"]:
        if old["opportunity_id"] == record["opportunity_id"]:
            raise FileExistsError("opportunity_id already exists; records are immutable")
        if record["identity_key"] and old.get("identity_key") == record["identity_key"] and old["kind"] == kind:
            # Keep complete immutable record snapshots; conflicts never silently pick a winner.
            history = old.setdefault("evidence_history", [])
            if not history:
                history.append(_record_snapshot(old))
            history.append(_record_snapshot(record))
            old.setdefault("requirement_conflicts", {})
            for field, value in record["requirements"].items():
                prior = old["requirements"].get(field)
                incoming_quote = record["requirement_quotes"].get(field)
                if field in old["requirement_conflicts"]:
                    candidates = list(old["requirement_conflicts"][field])
                    candidate = {"value": value, "citation": incoming_quote}
                    if value is not None and candidate not in candidates:
                        candidates.append(candidate)
                    old["requirement_conflicts"][field] = candidates
                    old["requirements"][field] = None
                    old["requirement_quotes"].pop(field, None)
                elif prior is not None and value is not None and prior != value:
                    old["requirement_conflicts"][field] = [
                        {"value": prior, "citation": old["requirement_quotes"].get(field)},
                        {"value": value, "citation": incoming_quote}]
                    old["requirements"][field] = None
                    old["requirement_quotes"].pop(field, None)
                elif value is not None and (prior is None or value == prior):
                    old["requirements"][field] = value
                    if incoming_quote:
                        old["requirement_quotes"][field] = incoming_quote
            old.setdefault("date_conflicts", {})
            for field in ("deadline", "published_at", "earliest_signal"):
                prior = old.get(field)
                incoming = record.get(field)
                existing_conflict = old["date_conflicts"].get(field)
                if existing_conflict is not None:
                    candidates = list(existing_conflict)
                    candidate = _citation_candidate(incoming)
                    if candidate and candidate not in candidates:
                        candidates.append(candidate)
                    old["date_conflicts"][field] = candidates
                    old[field] = None
                elif prior and incoming and prior["value"] != incoming["value"]:
                    old["date_conflicts"][field] = [
                        _citation_candidate(prior), _citation_candidate(incoming)]
                    old[field] = None
                elif prior is None and incoming is not None:
                    old[field] = incoming
                elif prior and incoming and prior["value"] == incoming["value"]:
                    incoming_acquired = _fresh_capture_time(record, incoming, assessment_time)
                    previous_acquired = _fresh_capture_time(old, prior, assessment_time)
                    if incoming_acquired is not None and (previous_acquired is None or incoming_acquired > previous_acquired):
                        old[field] = incoming
            if not old["date_conflicts"]:
                old.pop("date_conflicts", None)
            for capture_hash, descriptor in record["sources"].items():
                previous = old["sources"].get(capture_hash, {})
                old["sources"][capture_hash] = {
                    **descriptor, **{key: value for key, value in previous.items() if value is not None}}
            docs = {}
            for doc in [*old["documents"], *record["documents"]]:
                key = (doc.get("url"), doc.get("original_sha256"), doc.get("capture_sha256"))
                merged = docs.setdefault(key, {})
                merged.update({name: value for name, value in doc.items() if value is not None})
            old["documents"] = list(docs.values())
            for key in ("direct_buyer_orgs", "roles", "procurement_route", "buyer_type"):
                prior, incoming = old.get(key), record.get(key)
                if not incoming:
                    continue
                if not prior:
                    old[key] = incoming
                    if key in record["field_evidence"]:
                        old["field_evidence"][key] = record["field_evidence"][key]
                elif prior != incoming:
                    old.setdefault("buyer_conflicts", {})[key] = [prior, incoming]
                    if key == "buyer_type" and incoming in EXCLUDED_BUYER_TYPES:
                        old[key] = incoming  # fail closed: an exclusion is never silently dropped
            old["merged_opportunity_ids"] = sorted(set(old.get("merged_opportunity_ids", [])) | {record["opportunity_id"]})
            old["qualification_assessed_at"] = assessment_time.isoformat()
            old["qualification"] = _qualification(old, assessment_time)
            old["status"] = old["qualification"].get("lifecycle_status", old["kind"])
            old["record_hash"] = canonical_hash({key: value for key, value in old.items() if key != "record_hash"})
            manifest["updated_at"] = assessment_time.isoformat()
            manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return old
    manifest["opportunities"].append(record)
    manifest["opportunities"].sort(key=lambda row: (row["kind"], row["opportunity_id"]))
    manifest["updated_at"] = assessment_time.isoformat()
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def _link(text: str, url: str) -> str:
    safe = _safe_url(url)
    return f'<a href="{html.escape(safe, quote=True)}" rel="noreferrer">{html.escape(text)}</a>'


def _local_link(text: str, relative_path: str, workspace: Path, output_parent: Path) -> str:
    target = (workspace / relative_path).resolve()
    if workspace not in target.parents or not target.is_file():
        raise ValueError("retained local artifact path is missing or escapes workspace")
    href = Path(os.path.relpath(target, output_parent)).as_posix()
    return f'<a href="{html.escape(href, quote=True)}">{html.escape(text)}</a>'


def _verify_retained_sources(record: dict[str, Any], workspace: Path) -> None:
    for source in record.get("sources", {}).values():
        path = (workspace / source["capture_file"]).resolve()
        if workspace not in path.parents:
            raise ValueError("capture path escapes workspace")
        try:
            capture = load_capture(path)
        except (OSError, ValueError) as exc:
            raise ValueError(f"retained capture cannot be verified: {source['capture_file']}") from exc
        if capture.capture_hash != source["capture_hash"] or capture.content_sha256 != source["content_sha256"]:
            raise ValueError(f"retained capture hash mismatch: {source['capture_file']}")
    for document in record.get("documents", []):
        if not document.get("original_file"):
            continue
        path = (workspace / document["original_file"]).resolve()
        if workspace not in path.parents or not path.is_file():
            raise ValueError("retained original path is missing or escapes workspace")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != document.get("original_sha256"):
            raise ValueError(f"retained original hash mismatch: {document['original_file']}")

_CSS = (":root{--canvas:#F5F4EE;--subtle:#EEF4EF;--ink:#232B26;--muted:#59645D;--action:#126653;--rule:#C9D6CE;"
        "--unknown-bg:#EEF4EF;--verified-bg:#E2EDE7;--review-bg:#F3EEDF}"
        "@media(prefers-color-scheme:dark){:root{--canvas:#18221D;--subtle:#232F29;--ink:#F5F4EE;--muted:#CAD4CC;"
        "--action:#70D1AE;--rule:#3A4A41;--unknown-bg:#232F29;--verified-bg:#28362E;--review-bg:#3A3624}}"
        "body{font:16px Manrope,system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;"
        "color:var(--ink);background:var(--canvas)}a{color:var(--action)}"
        "nav,article,section{background:var(--subtle);padding:1rem;margin:1rem 0;border:1px solid var(--rule);"
        "border-radius:8px}nav a{margin-right:1.5rem}table{border-collapse:collapse;width:100%}"
        "td,th{border:1px solid var(--rule);padding:.5rem;text-align:left;vertical-align:top}"
        "code{font-family:'IBM Plex Mono',monospace;overflow-wrap:anywhere}blockquote{white-space:pre-wrap}"
        "small{overflow-wrap:anywhere}.brief{border-left:4px solid var(--action);padding-left:1rem}"
        ".verified{background:var(--verified-bg)}.unknown{background:var(--unknown-bg);color:var(--muted)}"
        ".review{background:var(--review-bg)}"
        ".tag{font:12px 'IBM Plex Mono',monospace;padding:.1rem .4rem;border-radius:4px}")


def _brief_html(brief: dict[str, Any]) -> str:
    qualification = brief["qualification"]
    rows = "".join(
        f"<li class='verified'><span class='tag'>VERIFIED</span> {html.escape(str(fact['field']))}: "
        f"{html.escape(str(fact['value']))} — <q>{html.escape(str(fact['quote']))}</q> "
        f"<small>{_link(fact['source_url'], fact['source_url']) if fact['source_url'] else 'source URL not recorded'}</small></li>"
        for fact in brief["facts"])
    inferred = "".join(
        f"<li class='review'><span class='tag'>INFERENCE</span> {html.escape(str(item['statement']))} "
        f"<small>({html.escape(item['basis'])})</small></li>" for item in brief["inferences"])
    unknown = "".join(
        f"<li class='unknown'><span class='tag'>UNKNOWN</span> {html.escape(item)}</li>" for item in brief["unknowns"])
    return ("<section class='brief'><h4>Operator brief</h4>"
            f"<p>{html.escape(brief['opportunity_type'])} · qualification <strong>"
            f"{html.escape(str(qualification['status']))}</strong> ("
            f"{html.escape(', '.join(qualification.get('reason_codes', [])))})</p>"
            f"<p><strong>Next action:</strong> {html.escape(brief['next_action'])}</p>"
            f"<ul>{rows}{inferred}{unknown}</ul></section>")


def render_workspace(workspace_dir: str | Path, output_file: str | Path) -> Path:
    workspace = Path(workspace_dir).resolve()
    manifest = _json(workspace / "workspace.json")
    target = Path(output_file).resolve()
    if workspace != target.parent and workspace not in target.parents:
        raise ValueError("workspace HTML output must be saved inside workspace")
    early, active, pending, expired = [], [], [], []
    details = []
    briefs: dict[str, dict[str, Any]] = {}
    for record in manifest.get("opportunities", []):
        expected_hash = record.get("record_hash")
        actual_hash = canonical_hash({key: value for key, value in record.items() if key != "record_hash"})
        if expected_hash != actual_hash:
            raise ValueError(f"opportunity record hash mismatch: {record.get('opportunity_id')}")
        draft_path = (workspace / record["response_workspace"]["draft_file"]).resolve()
        if workspace not in draft_path.parents:
            raise ValueError("draft path escapes workspace")
        draft = _json(draft_path)
        if draft.get("opportunity_id") != record["opportunity_id"]:
            raise ValueError("draft opportunity_id mismatch")
        qualification = _qualification(record, datetime.now(UTC))
        brief = build_brief(record, qualification)
        briefs[record["opportunity_id"]] = brief
        _verify_retained_sources(record, workspace)
        if record["kind"] == "PRE_RFP_PROJECT":
            early.append(record)
        elif qualification.get("lifecycle_status") == "OPEN_AS_OF_PUBLIC_SOURCE":
            active.append(record)
        elif qualification.get("lifecycle_status") == "EXPIRED":
            expired.append(record)
        else:
            pending.append(record)
        heading = html.escape(str(record.get("title") or record["opportunity_id"]))
        lifecycle = qualification.get("lifecycle_status", record["kind"])
        entries = [f"<h3>{heading}</h3>", f"<p>Lifecycle: <strong>{html.escape(str(lifecycle))}</strong> · Identity: {html.escape(record['identity_resolution'])}</p>"]
        entries.append(_brief_html(brief))
        entries.append(f"<p>Canonical project ID: <code>{html.escape(str(record.get('project_id') or 'UNKNOWN'))}</code> · First seen: {html.escape(str(record.get('first_seen_at') or 'UNKNOWN'))} · Vertical: {html.escape(str(record.get('vertical') or 'UNKNOWN'))}</p>")
        entries.append(f"<p>Signal family: {html.escape(str(record.get('signal_family') or 'UNKNOWN'))}; operator-supplied note (not derived): {html.escape(str(record['next_action']))}</p>")
        entries.append(f"<p>Power-gap hypothesis: {html.escape(str(record.get('power_gap_hypothesis') or 'UNKNOWN'))}</p>")
        entries.append(f"<p>Direct buyer organizations: {html.escape(', '.join(map(str, record.get('direct_buyer_orgs', []))) or 'UNKNOWN')}</p>")
        deadline = record.get("deadline")
        entries.append(f"<p>Deadline: {html.escape(str(deadline['value'])) if deadline else 'UNKNOWN'} {'' if record['kind'] == 'PRE_RFP_PROJECT' else ' · 2G fit: ' + html.escape(qualification['status']) + ' (' + html.escape(', '.join(qualification['reason_codes'])) + ')'}</p>")
        entries.append(f"<p>Amendments status: {html.escape(str(qualification.get('amendments_status', 'UNKNOWN')))} · Capture freshness: {html.escape(str(qualification.get('capture_fresh', 'UNKNOWN')))}</p>")
        entries.append("<p>Missing information: " + html.escape(", ".join(record.get("missing_information", [])) or "None identified") + "</p>")
        if record.get("earliest_signal"):
            entries.append(f"<p>Earliest signal: {html.escape(record['earliest_signal']['value'])} — {html.escape(record['earliest_signal']['quote'])}</p>")
        for field, candidates in record.get("date_conflicts", {}).items():
            rendered = "".join(
                "<li>" + html.escape(str(candidate.get("value") or "UNKNOWN")) + " — " +
                html.escape(str(candidate.get("quote") or "UNKNOWN")) + " · capture " +
                html.escape(str(candidate.get("capture_sha256") or "UNKNOWN")) + "</li>"
                for candidate in candidates)
            entries.append(f"<p>Date conflict: {html.escape(field)} — UNKNOWN; human review required.</p><ul>{rendered}</ul>")
        entries.append("<h4>Source evidence</h4><ul>")
        for source in record["sources"].values():
            local_capture = _local_link("Local capture", source["capture_file"], workspace, target.parent)
            entries.append(f"<li>{_link(source.get('title') or source['source_url'], source['source_url'])} · {local_capture} · content SHA-256 <code>{html.escape(source['content_sha256'])}</code> · capture hash <code>{html.escape(source['capture_hash'])}</code></li>")
        entries.append("</ul><h4>Requirements and compliance</h4><table><tr><th>Field</th><th>Value</th><th>Source excerpt</th></tr>")
        for key, value in record["requirements"].items():
            if key == "deadline":
                continue
            citation = record["requirement_quotes"].get(key)
            value_text = "UNKNOWN" if value is None or value == [] else str(value)
            if key in record.get("requirement_conflicts", {}):
                value_text = "CONFLICT - HUMAN REVIEW REQUIRED"
            quote = f"{citation['quote']} · {citation['capture_sha256']}" if citation else "UNKNOWN"
            entries.append(f"<tr><td>{html.escape(key)}</td><td>{html.escape(value_text)}</td><td>{html.escape(quote)}</td></tr>")
        deadline_evidence = record.get("deadline")
        deadline_value = deadline_evidence.get("value", "UNKNOWN") if deadline_evidence else "UNKNOWN"
        deadline_quote = (f"{deadline_evidence['quote']} · {deadline_evidence['capture_sha256']}"
                          if deadline_evidence else "UNKNOWN")
        entries.append(f"<tr><td>deadline</td><td>{html.escape(str(deadline_value))}</td><td>{html.escape(deadline_quote)}</td></tr>")
        entries.append("</table><h4>Documents</h4><ul>")
        for doc in record["documents"]:
            label = doc.get("title") or doc["url"]
            suffix = f" (original SHA-256 {doc['original_sha256']})" if doc.get("original_sha256") else ""
            local_link = ""
            if doc.get("original_file"):
                local_link = " · " + _local_link("Retained original", doc["original_file"], workspace, target.parent)
            entries.append(f"<li>{_link(label, doc['url'])}{html.escape(suffix)}{local_link}</li>")
        entries.append("</ul><h4>RFP workspace</h4><p>Draft placeholders are editable in " + html.escape(record["response_workspace"]["draft_file"]) + ". Completion: " + html.escape(str(draft.get("completion_state", "UNKNOWN"))) + "</p>")
        entries.append("<ul>" + "".join(f"<li>{html.escape(str(line))}</li>" for line in draft.get("outline", [])) + "</ul>")
        entries.append("<h4>Draft fields</h4><dl>" + "".join(
            f"<dt>{html.escape(str(key))}</dt><dd>{html.escape(str(value)) or 'UNKNOWN'}</dd>"
            for key, value in draft.get("draft_placeholders", {}).items()) + "</dl>")
        entries.append("<h4>Unanswered questions</h4><ul>" + "".join(
            f"<li>{html.escape(str(question))}</li>" for question in draft.get("unanswered_questions", [])) + "</ul>")
        entries.append(f"<h4>Operator notes and caveats</h4><p>{html.escape(str(record.get('notes') or 'UNKNOWN'))}</p>")
        for key, item in record["field_evidence"].items():
                entries.append(f"<details><summary>{html.escape(key)} evidence</summary><blockquote>{html.escape(item['quote'])}</blockquote><small>SHA-256 {html.escape(item['capture_sha256'])}</small></details>")
        for key, conflict in record.get("requirement_conflicts", {}).items():
            entries.append(f"<p>Requirement conflict: {html.escape(key)} requires human review ({len(conflict)} source-backed values).</p>")
        detail_id = html.escape(_ID.sub("-", record["opportunity_id"]), quote=True)
        details.append(f"<article id='{detail_id}'>" + "".join(entries) + "</article>")
    def section(title: str, records: list[dict[str, Any]]) -> str:
        cards = []
        for row in records:
            anchor = html.escape(_ID.sub("-", row["opportunity_id"]), quote=True)
            buyer = ", ".join(map(str, row.get("direct_buyer_orgs", []))) or row.get("identity", {}).get("organization") or "UNKNOWN"
            due = (row.get("deadline") or {}).get("value", "UNKNOWN")
            summary = row.get("power_gap_hypothesis") or row.get("requirements", {}).get("scope") or "UNKNOWN"
            cards.append(f"<article><h3><a href='#{anchor}'>{html.escape(str(row.get('title') or row['opportunity_id']))}</a></h3><p>Buyer: {html.escape(str(buyer))}</p><p>Deadline: {html.escape(str(due))}</p><p>Power need: {html.escape(str(summary))}</p><p>Type: {html.escape(briefs[row['opportunity_id']]['opportunity_type'])} · {html.escape(str(briefs[row['opportunity_id']]['qualification']['status']))}</p><p>Next: {html.escape(briefs[row['opportunity_id']]['next_action'])}</p></article>")
        return f"<section><h2>{title} ({len(records)})</h2>" + ("".join(cards) or "<p>None recorded</p>") + "</section>"
    page = "<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Trailforge Opportunity Workspace</title><style>" + _CSS + "</style><h1>Trailforge Opportunity Workspace</h1><p>Reviewed source evidence only. UNKNOWN fields remain unanswered. No contact or submission is performed.</p><nav><a href='#early'>EARLY PROJECTS</a><a href='#active'>ACTIVE RFPs</a><a href='#pending'>RFPs NEEDING REVIEW</a><a href='#expired'>EXPIRED RFPs</a><a href='#workspace'>RFP WORKSPACE</a><a href='#signal-lab'>SIGNAL LAB</a></nav><div id='early'>" + section("EARLY PROJECTS", early) + "</div><div id='active'>" + section("ACTIVE RFPs", active) + "</div><div id='pending'>" + section("RFPs NEEDING REVIEW", pending) + "</div><div id='expired'>" + section("EXPIRED RFPs", expired) + "</div><div id='workspace'><h2>RFP WORKSPACE</h2>" + "".join(details) + "</div><section id='signal-lab'><h2>SIGNAL LAB</h2><p>Use the existing Trailforge UI and evidence trace commands for temporal signal review. This workspace links the evidence and next action without changing simulation semantics.</p></section></html>"
    target.parent.mkdir(parents=True, exist_ok=True)
    page = "\n".join(line.rstrip() for line in page.splitlines()) + "\n"
    target.write_text(page, encoding="utf-8")
    return target
