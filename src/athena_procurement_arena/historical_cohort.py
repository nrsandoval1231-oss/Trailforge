"""Fail-closed adapter for small, source-cited historical project cohorts."""
from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime, time
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .public_capture import PublicCapture, load_capture
from .signal_ledger import EvidenceClass, ProjectSignal, ProjectTrace, SignalType, write_trace
from .trace_backtest import backtest_traces

SCHEMA = "trailforge-historical-cohort-input-v1"
IDENTITY_STATES = {"RESOLVED", "UNRESOLVED"}
PUBLISHED_DATE_BASES = {"DISPLAYED_SOURCE_DATE_NOT_VERIFIED_AVAILABILITY", "DOCUMENT_ISSUE_DATE_NOT_WEB_PUBLICATION"}
AVAILABILITY_BASES = {"ARCHIVED_CONTENT", "OFFICIAL_PUBLICATION_TIMESTAMP", "CURRENT_CAPTURE"}


def _date_interval(value: str | None, precision: str | None) -> tuple[datetime, datetime] | None:
    if value is None:
        if precision is not None:
            raise ValueError("published_date_precision requires published_at")
        return None
    if precision == "day":
        day = date.fromisoformat(value)
        return datetime.combine(day, time.min), datetime.combine(day, time.max)
    if precision == "instant":
        instant = datetime.fromisoformat(value)
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("published_at instant must be timezone-aware")
        instant = instant.astimezone(UTC).replace(tzinfo=None)
        return instant, instant
    raise ValueError("published_date_precision must be 'day' or 'instant'")


def _load_proof(root: Path, capture_path: str, excerpt: str, url: str | None = None) -> tuple[PublicCapture, str]:
    if not capture_path or not excerpt:
        raise ValueError("source capture path and exact evidence excerpt are required")
    path = (root / capture_path).resolve()
    if root.resolve() not in path.parents:
        raise ValueError("capture path must remain under the input directory")
    capture = load_capture(path)
    if url and capture.source_url != url:
        raise ValueError("capture URL does not match cited source URL")
    if excerpt not in capture.content:
        raise ValueError("exact excerpt is absent from source capture")
    return capture, sha256(capture.content.encode("utf-8")).hexdigest()


def _parse_instant(value: str | None, field: str) -> datetime | None:
    if value is None:
        return None
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return result.astimezone(UTC)


def _availability(root: Path, item: dict[str, Any], source_capture: PublicCapture, source_hash: str) -> tuple[datetime | None, dict[str, Any]]:
    raw_time = item.get("available_at")
    basis = item.get("availability_basis")
    if raw_time is None:
        if any(item.get(key) for key in ("availability_basis", "availability_capture_path", "availability_excerpt", "availability_time_excerpt")):
            raise ValueError("availability evidence fields require available_at")
        return None, {"status": "UNKNOWN", "reason": "historical availability unsupported"}
    availability = _parse_instant(raw_time, "available_at")
    if basis not in AVAILABILITY_BASES:
        raise ValueError("availability_basis must be an allowed evidence class")
    archive_path = item.get("availability_capture_path")
    excerpt = item.get("availability_excerpt")
    time_excerpt = item.get("availability_time_excerpt")
    if not archive_path or not excerpt or not time_excerpt:
        raise ValueError("availability requires capture, exact content excerpt, and raw timestamp excerpt")
    capture, capture_hash = _load_proof(root, archive_path, excerpt, item.get("availability_capture_url"))
    if item["excerpt"] not in capture.content:
        raise ValueError("availability capture does not contain the cited signal text")
    now = datetime.now(UTC)
    if source_capture.captured_at > now:
        raise ValueError("source capture postdates current run")
    if capture.captured_at > now:
        raise ValueError("availability capture postdates current run")
    if availability > capture.captured_at or availability > source_capture.captured_at:
        raise ValueError("available_at postdates a cited evidence capture")
    status, reason = "UNKNOWN", "availability evidence did not prove historical public availability"
    if basis == "ARCHIVED_CONTENT":
        parsed = urlparse(capture.source_url)
        if parsed.hostname != "web.archive.org":
            raise ValueError("ARCHIVED_CONTENT requires a web.archive.org capture URL")
        match = re.match(r"^/web/(\d{14})/(https?://.+)$", unquote(parsed.path))
        if not match:
            raise ValueError("ARCHIVED_CONTENT capture URL must contain a 14-digit Wayback timestamp and original URL")
        stamp, original_url = match.groups()
        if original_url.rstrip("/") != item["source_url"].rstrip("/"):
            raise ValueError("archive original URL does not match signal source_url")
        if time_excerpt != stamp or stamp not in capture.content:
            raise ValueError("availability_time_excerpt must exactly match a timestamp in archived capture content")
        archive_time = datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
        if availability != archive_time:
            raise ValueError("available_at must equal the timestamp encoded in the archive URL")
        status, reason = "SUPPORTED", None
    elif basis == "OFFICIAL_PUBLICATION_TIMESTAMP":
        if capture.source_url != item["source_url"]:
            raise ValueError("official timestamp capture URL must match the cited source URL")
        if time_excerpt not in capture.content:
            raise ValueError("availability_time_excerpt is absent from cited capture")
        parsed_time = _parse_instant(time_excerpt, "availability_time_excerpt")
        if parsed_time != availability:
            raise ValueError("available_at must equal the explicit timezone-aware timestamp excerpt")
        status, reason = "SUPPORTED", None
    return availability if status == "SUPPORTED" else None, {
        "status": status, "reason": reason, "basis": basis, "capture_path": archive_path,
        "capture_sha256": capture_hash, "excerpt": excerpt, "time_excerpt": time_excerpt,
        "availability_at": availability.isoformat(), "source_capture_sha256": source_hash,
    }


def _report_markdown(report: dict[str, Any]) -> str:
    lines = ["# HC-001 historical cohort", "", f"{report['project_count']} purposive cases; descriptive only, not a representative or negative cohort.",
             f"Fixed policy selection basis: {report['policy']['selection_basis']}",
             "Source dates are diagnostics and do not establish historical availability. Strict lead time is UNKNOWN unless both timestamps are proven.", "",
             "| Project | Earliest source date (basis) | Earliest supported availability | Fixed-policy surface | Milestone | Strict lead | Buyer path |",
             "|---|---|---|---|---|---|---|"]
    for case in report["cases"]:
        first = case.get("earliest_dated_source") or {}
        surface = case.get("first_valid_policy_surface_at") or "UNKNOWN"
        milestone = case.get("conventional_milestone_available_at") or "UNKNOWN"
        lead = f"{case['lead_time_seconds']} seconds" if case.get("lead_time_seconds") is not None else "UNKNOWN"
        buyer = case["buyer_path"].get("stated_organization") or "UNKNOWN"
        lines.append(f"| {case['project_id']} | {first.get('value', 'UNKNOWN')} ({first.get('basis', 'UNKNOWN')}) | {case.get('earliest_available_signal_at') or 'UNKNOWN'} | {surface} | {milestone} | {lead} | {buyer} (availability {case['buyer_path']['status']}) |")
    lines += ["", "## Case notes", ""]
    for case in report["cases"]:
        lines.append(f"- **{case['project_id']}** ({case['identity_status']}): {case.get('notes') or 'No case note supplied.'}")
        diagnostic = case.get("diagnostic_published_date_comparison")
        if diagnostic:
            span = diagnostic["lead_interval_seconds"]
            lines.append(f"  Published-date interval diagnostic: {span[0]} to {span[1]} seconds ({diagnostic['status']}; timezone {diagnostic['timezone_status']}).")
    lines += ["", "No model performance or signal-promotion claim is made. Buyer organizations may be identified in source material while historical buyer availability remains UNKNOWN.", ""]
    return "\n".join(lines)


def build_historical_report(input_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    """Validate citations, replay strictly supported signals, and retain every case."""
    source = Path(input_path).resolve()
    root = source.parent
    input_bytes = source.read_bytes()
    raw = json.loads(input_bytes)
    if raw.get("schema_version") != SCHEMA:
        raise ValueError(f"unsupported schema_version; expected {SCHEMA}")
    policy = raw["policy"]
    target_type = SignalType(policy["target_signal_type"])
    early_types = tuple(SignalType(item) for item in policy["early_signal_types"])
    if not early_types or len(set(early_types)) != len(early_types) or not policy.get("selection_basis"):
        raise ValueError("fixed policy requires unique early_signal_types and selection_basis")
    projects = raw["projects"]
    ids = [item["project_id"] for item in projects]
    if len(ids) != len(set(ids)):
        raise ValueError("project IDs must be unique")
    traces: list[ProjectTrace] = []
    cases: list[dict[str, Any]] = []
    for project in projects:
        identity = project.get("identity_status")
        if identity not in IDENTITY_STATES:
            raise ValueError("identity_status must be RESOLVED or UNRESOLVED")
        candidate_signals: dict[str, ProjectSignal] = {}
        signal_rows: list[dict[str, Any]] = []
        signal_by_id: dict[str, dict[str, Any]] = {}
        seen_signal_ids: set[str] = set()
        for item in project.get("signals", []):
            if item["signal_id"] in seen_signal_ids:
                raise ValueError(f"duplicate signal_id in project {project['project_id']}: {item['signal_id']}")
            seen_signal_ids.add(item["signal_id"])
            signal_type = SignalType(item["signal_type"])
            source_capture, source_hash = _load_proof(root, item.get("source_capture_path"), item.get("excerpt"), item.get("source_url"))
            if item.get("source_sha256") != source_hash:
                raise ValueError(f"source_sha256 does not match captured source: {item['signal_id']}")
            pub_interval = _date_interval(item.get("published_at"), item.get("published_date_precision"))
            published_basis = item.get("published_date_basis")
            if pub_interval and published_basis not in PUBLISHED_DATE_BASES:
                raise ValueError("published_date_basis must identify displayed source date or document issue date")
            if pub_interval:
                _load_proof(root, item["source_capture_path"], item.get("published_date_excerpt"), item["source_url"])
            elif item.get("published_date_excerpt"):
                raise ValueError("published date evidence fields require published_at")
            availability_time, availability_proof = _availability(root, item, source_capture, source_hash)
            contradictory = bool(availability_time and pub_interval and availability_time.replace(tzinfo=None) < pub_interval[0])
            if contradictory:
                availability_time = None
                availability_proof = {**availability_proof, "status": "UNKNOWN", "reason": "availability predates stated publication timestamp"}
            available = bool(availability_time and identity == "RESOLVED")
            if identity != "RESOLVED" and availability_proof["status"] == "SUPPORTED":
                availability_proof = {**availability_proof, "status": "UNKNOWN", "reason": "project identity unresolved"}
            row = {
                "signal_id": item["signal_id"], "signal_type": signal_type.value, "title": item["title"],
                "published_at": item.get("published_at"), "published_date_precision": item.get("published_date_precision"),
                "published_date_basis": published_basis, "published_date_excerpt": item.get("published_date_excerpt"),
                "available_at": availability_time.isoformat() if available else None,
                "availability_status": "SUPPORTED" if available else "UNKNOWN", "availability_reason": availability_proof.get("reason"),
                "source_url": item["source_url"], "source_capture_path": item["source_capture_path"],
                "source_capture_sha256": source_hash, "excerpt": item["excerpt"],
                "availability_basis": availability_proof.get("basis"), "availability_capture_path": availability_proof.get("capture_path"),
                "availability_capture_sha256": availability_proof.get("capture_sha256"), "availability_excerpt": availability_proof.get("excerpt"),
                "availability_time_excerpt": availability_proof.get("time_excerpt"),
                "diagnostic_published_interval": [x.isoformat() for x in pub_interval] if pub_interval else None,
                "diagnostic_timezone_status": "UNKNOWN" if item.get("published_date_precision") == "day" else ("SOURCE_TIMEZONE" if pub_interval else None),
            }
            signal_rows.append(row)
            signal_by_id[item["signal_id"]] = row
            if available:
                candidate_signals[item["signal_id"]] = ProjectSignal(
                    signal_id=item["signal_id"], project_id=project["project_id"], observed_at=availability_time,
                    signal_type=signal_type, title=item["title"], evidence_class=EvidenceClass.PUBLIC,
                    source_sha256=source_hash, verified_by="agent-assisted-extraction-pending-independent-semantic-review",
                    claims={"historical_availability_basis": availability_proof.get("basis")},
                    source_url=item["source_url"], source_quote=item["excerpt"],
                )
        milestone_id = project.get("conventional_milestone_signal_id")
        if not milestone_id or milestone_id not in signal_by_id:
            raise ValueError(f"conventional_milestone_signal_id must reference a supplied signal: {project['project_id']}")
        milestone = signal_by_id[milestone_id]
        if milestone["signal_type"] != target_type.value:
            raise ValueError("conventional milestone signal must have the fixed policy target_signal_type")
        # Restrict each replay trace to policy early signals plus the explicitly selected target.
        replay_signals = [signal for signal in candidate_signals.values()
                          if signal.signal_type in early_types or signal.signal_id == milestone_id]
        if identity == "RESOLVED" and replay_signals:
            traces.append(ProjectTrace(project["project_id"], tuple(sorted(replay_signals, key=lambda x: (x.observed_at, x.signal_id)))))
        early_rows = [row for row in signal_rows if row["signal_type"] in {item.value for item in early_types}]
        dated_sources = [row for row in signal_rows if row["diagnostic_published_interval"]]
        earliest_dated = min(dated_sources, key=lambda row: (row["diagnostic_published_interval"][0], row["signal_id"])) if dated_sources else None
        available_sources = [row for row in signal_rows if row["availability_status"] == "SUPPORTED"]
        earliest_available = min(available_sources, key=lambda row: (row["available_at"], row["signal_id"])) if available_sources else None
        target_time = _parse_instant(milestone["available_at"], "milestone.available_at") if milestone["available_at"] else None
        valid_surfaces = [row for row in early_rows if row["availability_status"] == "SUPPORTED" and target_time
                          and _parse_instant(row["available_at"], "signal.available_at") < target_time]
        first_surface = min(valid_surfaces, key=lambda row: (row["available_at"], row["signal_id"])) if valid_surfaces else None
        diagnostic_early = [row for row in early_rows if row["diagnostic_published_interval"]]
        target_pub = milestone["diagnostic_published_interval"]
        diagnostic_published_lead = None
        if diagnostic_early and target_pub:
            first_pub = min(diagnostic_early, key=lambda row: row["diagnostic_published_interval"][0])
            low = datetime.fromisoformat(target_pub[0]) - datetime.fromisoformat(first_pub["diagnostic_published_interval"][1])
            high = datetime.fromisoformat(target_pub[1]) - datetime.fromisoformat(first_pub["diagnostic_published_interval"][0])
            diagnostic_published_lead = {"earliest_policy_signal_id": first_pub["signal_id"],
                                         "lead_interval_seconds": [int(low.total_seconds()), int(high.total_seconds())],
                                         "status": "DIAGNOSTIC_ONLY_NOT_VALIDATED_LEAD_TIME", "timezone_status": "UNKNOWN"}
        buyer = project.get("buyer_path", {})
        buyer_capture, buyer_hash = _load_proof(root, buyer.get("evidence_capture_path"), buyer.get("excerpt"))
        buyer_time = _parse_instant(buyer.get("available_at"), "buyer_path.available_at")
        if buyer_time is None and any(buyer.get(key) for key in ("availability_basis", "availability_capture_path", "availability_excerpt", "availability_time_excerpt")):
            raise ValueError("buyer availability evidence fields require available_at")
        buyer_time_proven = None
        if buyer_time and buyer.get("availability_basis"):
            buyer_item = {
                "available_at": buyer.get("available_at"), "availability_basis": buyer.get("availability_basis"),
                "availability_capture_path": buyer.get("availability_capture_path"),
                "availability_excerpt": buyer.get("availability_excerpt"),
                "availability_time_excerpt": buyer.get("availability_time_excerpt"),
                "availability_capture_url": buyer.get("availability_capture_url"),
                "source_url": buyer.get("source_url", buyer_capture.source_url), "excerpt": buyer["excerpt"],
            }
            buyer_time_proven, _ = _availability(root, buyer_item, buyer_capture, buyer_hash)
        buyer_supported = bool(identity == "RESOLVED" and buyer_time_proven and first_surface
                               and buyer_time_proven <= _parse_instant(first_surface["available_at"], "surface.available_at")
                               and buyer.get("organization"))
        cases.append({
            "project_id": project["project_id"], "identity_status": identity, "identity_basis": project.get("identity_basis"),
            "notes": project.get("notes"), "signals": signal_rows, "conventional_milestone_signal_id": milestone_id,
            "earliest_dated_source": {"signal_id": earliest_dated["signal_id"], "value": earliest_dated["published_at"],
                                      "precision": earliest_dated["published_date_precision"], "basis": earliest_dated["published_date_basis"]} if earliest_dated else None,
            "earliest_available_signal_id": earliest_available["signal_id"] if earliest_available else None,
            "earliest_available_signal_at": earliest_available["available_at"] if earliest_available else None,
            "conventional_milestone_available_at": milestone["available_at"],
            "conventional_milestone_status": milestone["availability_status"],
            "first_valid_policy_surface_signal_id": first_surface["signal_id"] if first_surface else None,
            "first_valid_policy_surface_at": first_surface["available_at"] if first_surface else None,
            "first_valid_policy_surface_status": "SUPPORTED" if first_surface else "UNKNOWN",
            "lead_time_seconds": int((target_time - _parse_instant(first_surface["available_at"], "surface.available_at")).total_seconds()) if first_surface and target_time else None,
            "diagnostic_published_date_comparison": diagnostic_published_lead,
            "buyer_path": {"status": "SUPPORTED" if buyer_supported else "UNKNOWN",
                           "stated_organization": buyer.get("organization"), "stated_status": buyer.get("status"),
                           "organization": buyer.get("organization") if buyer_supported else None,
                           "available_at": buyer_time_proven.isoformat() if buyer_supported else None,
                           "evidence_capture_path": buyer.get("evidence_capture_path"), "evidence_capture_sha256": buyer_hash,
                           "excerpt": buyer.get("excerpt")},
        })
    replay = backtest_traces(tuple(traces), target_signal_type=target_type, early_signal_types=early_types) if traces else None
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError(f"HC-001 output directory must be new and empty: {output}")
    trace_files = []
    for trace in traces:
        filename = f"{sha256(trace.project_id.encode()).hexdigest()[:16]}.trace.json"
        write_trace(trace, output / filename)
        trace_files.append({"project_id": trace.project_id, "path": filename, "trace_hash": trace.trace_hash})
    report = {
        "schema_version": "trailforge-historical-cohort-report-v1", "cohort_id": raw["cohort_id"],
        "input_schema_version": SCHEMA, "input_sha256": sha256(input_bytes).hexdigest(),
        "review_status": "agent-assisted extraction; independent semantic review pending; no human approval asserted",
        "policy": {"target_signal_type": target_type, "early_signal_types": list(early_types), "selection_basis": policy["selection_basis"]},
        "project_count": len(cases), "eligible_trace_count": len(traces), "cases": cases,
        "trace_files": trace_files, "replay": replay.as_dict() if replay else None,
        "metrics_scope": "Descriptive convenience cohort only; no predictive quality or policy promotion claim.",
    }
    (output / "report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (output / "report.md").write_text(_report_markdown(report), encoding="utf-8")
    return report
