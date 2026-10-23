"""Mechanically check cohort dossiers so unreviewed research cannot carry invented evidence.

Dossiers (`trailforge-cohort-dossier-v0`) are PROPOSALS.  This checker never marks one reviewed.  It checks that
every quote exists verbatim in the STORED capture file, that the capture file is self-consistent (content hash and
capture hash recomputed by the repo loader), and that dates, confidence and lead-time arithmetic are internally
consistent.  It cannot prove that a capture is a faithful copy of the live source (captures carry provider
"firecrawl" with an empty provider_job_id, so there is no independent receipt), nor that a quote means what the
dossier says.  A named human must still re-fetch or diff samples before accepting a case.
See docs/COHORT_INTAKE.md.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from athena_procurement_arena.public_capture import PublicCapture, load_capture  # noqa: E402
from athena_procurement_arena.signal_ledger import SignalType  # noqa: E402

SCHEMA_VERSION = "trailforge-cohort-dossier-v0"
DEFAULT_ROOT = "research/cohort-intake"
STATUSES = ("PROPOSED_UNREVIEWED", "INCOMPLETE")
VERTICALS = ("us-mining", "intl-mining", "data-center", "utility-institutional")
CONFIDENCES = ("PROOF_CITED", "PRINTED_DATE_ONLY", "UNKNOWN")
EVIDENCE_KINDS = (
    "sec_edgar", "exchange_announcement", "government_docket", "wayback_cdx", "wire_timestamp", "printed_date", "other",
)
UNPROVEN_KINDS = ("printed_date", "other")
ROLES = ("OWNER", "DEVELOPER", "EPC", "EPCM", "GC", "ELECTRICAL_CONTRACTOR", "UTILITY", "OTHER")
BASES = ("PROOF_CITED_TIMESTAMPS", "UNVERIFIED")
TARGET_FITS = (
    "TEMPORARY_OR_RENTAL", "BRIDGE_OR_INTERIM", "ONSITE_LONG_TERM_SUPPLY", "PERMANENT_PLANT_OR_GRID",
    "PERMIT_OR_STATUS_ONLY",
)
WEAK_TARGET_FITS = ("PERMANENT_PLANT_OR_GRID", "PERMIT_OR_STATUS_ONLY")
LEGACY_TOKENS = {"VERIFIED_TIMESTAMP": "PROOF_CITED", "VERIFIED_TIMESTAMPS": "PROOF_CITED_TIMESTAMPS"}
PROJECT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,79}$")
SHA256_HEX = re.compile(r"^[0-9a-fA-F]{64}$")
WAYBACK_SNAPSHOT = re.compile(r"^https?://web\.archive\.org/web/\d{14}id_/")
# A string that is only a review/verification status word (trailing punctuation ignored).
STATUS_CLAIM = re.compile(
    r"^(human[\s_-]*)?(verified\w*|reviewed|approved|confirmed|signed[\s_-]*off)$", re.IGNORECASE)
# Keys that assert a review or sign-off.  Keys starting with "unverified" are fine.
SIGN_OFF_KEY = re.compile(
    r"^(?!unverified)(.*verified.*|reviewed|approved|review|human_review|signed_off|reviewed_by|approved_by|signed_by)$")
HARD_MIN_QUOTE = 20
MIN_QUOTE = 40
MIN_YEAR = 1990
TOLERANCE_DAYS = 0.01
MIN_FIT_NOTE = 20

TOP_KEYS = (
    "schema_version", "status", "project_id", "project_name", "vertical", "location", "owner_or_developer",
    "selection_note", "signals", "target", "buyer_path", "lead_time", "blockers", "reviewer_checklist",
    "created_by", "created_at",
)
TOP_OPTIONAL = ("target_fit", "target_fit_note", "later_procurement_events")
SIGNAL_KEYS = (
    "signal_id", "signal_type", "title", "observed_at", "availability_confidence", "availability_evidence",
    "source_url", "capture_path", "capture_id", "source_sha256", "source_quote", "claims",
)
EVIDENCE_KEYS = ("kind", "url", "note")
BUYER_KEYS = ("organization", "role", "evidence_signal_id", "quote")
LEAD_KEYS = ("days", "basis", "earliest_signal_id", "note")


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _loads_strict(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_no_duplicate_keys)


@dataclass
class Report:
    path: str
    project_id: str = ""
    vertical: str = ""
    status: str = ""
    signals: int = 0
    has_target: bool = False
    basis: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    urls: set[str] = field(default_factory=set)

    def as_dict(self) -> dict[str, Any]:
        return {
            "file": self.path, "project_id": self.project_id, "vertical": self.vertical, "status": self.status,
            "signals": self.signals, "target": self.has_target, "lead_time_basis": self.basis,
            "passed": not self.errors, "errors": self.errors, "warnings": self.warnings,
        }


@dataclass
class Checked:
    """What later cross-checks need from a signal that parsed."""
    signal_id: str
    observed_at: datetime | None
    confidence: str
    capture: PublicCapture | None


class Context:
    def __init__(self, repo_root: Path, now: datetime):
        self.repo_root = repo_root.resolve()
        self.now = now
        self._captures: dict[tuple[str, str], PublicCapture | str] = {}

    def capture(self, capture_path: str, vertical: str) -> PublicCapture | str:
        """Load a capture through the repo loader; a str result is the error message."""
        key = (capture_path, vertical)
        if key not in self._captures:
            self._captures[key] = self._load(capture_path, vertical)
        return self._captures[key]

    def _load(self, capture_path: str, vertical: str) -> PublicCapture | str:
        posix = PurePosixPath(capture_path)
        if (not capture_path or "\\" in capture_path or posix.is_absolute() or capture_path.startswith("//")
                or re.match(r"^[A-Za-z]:", capture_path) or ".." in posix.parts):
            return f"capture_path must be a repo-relative POSIX path with no '..' (got {capture_path!r})"
        resolved = (self.repo_root / posix).resolve()
        if not resolved.is_relative_to(self.repo_root):
            return f"capture_path resolves outside the repository: {capture_path}"
        if vertical in VERTICALS:
            allowed = self.repo_root / DEFAULT_ROOT / vertical / "captures"
            if not resolved.is_relative_to(allowed):
                return f"capture_path must be inside {DEFAULT_ROOT}/{vertical}/captures/ (got {capture_path})"
        if not resolved.is_file():
            return f"capture file does not exist: {capture_path}"
        try:
            _loads_strict(resolved.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return f"capture {capture_path} is not strictly valid JSON: {exc}"
        try:
            return load_capture(resolved)
        except Exception as exc:  # the loader raises ValueError/KeyError/JSONDecodeError for any bad capture
            return f"capture {capture_path} failed the repo capture loader: {type(exc).__name__}: {exc}"


def _parse_time(value: Any, where: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}: must be an ISO-8601 string with timezone")
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{where}: not a valid ISO-8601 datetime: {value!r}")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{where}: datetime must be timezone-aware (naive datetime {value!r})")
        return None
    if parsed.year < MIN_YEAR:
        errors.append(f"{where}: year {parsed.year} is before {MIN_YEAR}")
        return None
    return parsed


def _text(obj: dict[str, Any], key: str, where: str, errors: list[str], *, empty_ok: bool = False) -> str | None:
    value = obj.get(key)
    if not isinstance(value, str) or (not empty_ok and not value.strip()):
        errors.append(f"{where}.{key}: must be a {'string' if empty_ok else 'non-empty string'}")
        return None
    return value


def _enum(obj: dict[str, Any], key: str, allowed: tuple[str, ...], where: str, errors: list[str]) -> str | None:
    value = obj.get(key)
    if isinstance(value, str) and value in LEGACY_TOKENS:
        errors.append(f"{where}.{key}: {value} was renamed to {LEGACY_TOKENS[value]} "
                      "(the token is agent-asserted proof, not human verification)")
        return None
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{where}.{key}: {value!r} is not one of {', '.join(allowed)}")
        return None
    return value


def _exact_keys(obj: dict[str, Any], keys: tuple[str, ...], where: str, errors: list[str], extra: tuple[str, ...] = ()
                ) -> None:
    allowed = set(keys) | set(extra)
    for key in sorted(set(keys) - set(obj)):
        errors.append(f"{where}: missing required field '{key}'")
    for key in sorted(set(obj) - allowed):
        errors.append(f"{where}: unexpected field '{key}'")


def _scan_status_claims(value: Any, where: str, errors: list[str]) -> None:
    """Reject sign-off keys and any string that claims verified/reviewed status."""
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and SIGN_OFF_KEY.match(key.casefold().replace("-", "_")):
                errors.append(f"{where}.{key}: reviewer sign-off/verified key is forbidden in an unreviewed dossier")
            _scan_status_claims(child, f"{where}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_status_claims(child, f"{where}[{index}]", errors)
    elif isinstance(value, str):
        if value in LEGACY_TOKENS and where.endswith((".availability_confidence", ".basis")):
            return  # reported with a rename hint by the enum check
        if STATUS_CLAIM.match(value.strip().strip(".!?;:, ")):
            errors.append(f"{where}: string {value!r} claims verified/reviewed status; only a named human may do that")


def _check_quote(quote: Any, capture: PublicCapture | None, where: str, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(quote, str) or not quote.strip():
        errors.append(f"{where}: quote must be a non-empty string")
        return
    if len(quote) < HARD_MIN_QUOTE:
        errors.append(f"{where}: quote is only {len(quote)} chars; minimum is {HARD_MIN_QUOTE}")
    elif len(quote) < MIN_QUOTE:
        warnings.append(f"{where}: quote is only {len(quote)} chars (< {MIN_QUOTE}); weak evidence")
    if capture is not None and quote not in capture.content:
        errors.append(
            f"{where}: quote is not an exact contiguous substring of capture {capture.capture_id} "
            f"(no whitespace or case normalization is applied): {quote[:80]!r}")


def _numbers(value: Any, where: str) -> list[tuple[str, str]]:
    """Numeric claim values as (path, digit string)."""
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            found += _numbers(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found += _numbers(child, f"{where}[{index}]")
    elif isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value):
        found.append((where, str(int(value)) if float(value).is_integer() else repr(float(value))))
    return found


def _check_claims(sig: dict[str, Any], where: str, warnings: list[str]) -> None:
    claims, quote = sig.get("claims"), sig.get("source_quote")
    if not isinstance(claims, dict) or not isinstance(quote, str):
        return
    plain = quote.replace(",", "")
    for path, digits in _numbers(claims, f"{where}.claims"):
        if digits not in plain:
            warnings.append(f"{path}: claim not literally supported by quote (value {digits} not found in source_quote)")


def _check_signal(sig: Any, where: str, vertical: str, ctx: Context, errors: list[str], warnings: list[str],
                  report: Report, *, target: bool) -> Checked | None:
    if not isinstance(sig, dict):
        errors.append(f"{where}: must be an object")
        return None
    _exact_keys(sig, SIGNAL_KEYS, where, errors, ("target_description",) if target else ())
    signal_id = _text(sig, "signal_id", where, errors)
    where = f"{where}[{signal_id}]" if signal_id else where
    signal_type = _enum(sig, "signal_type", tuple(item.value for item in SignalType), where, errors)
    if target and signal_type is not None and signal_type != SignalType.PROCUREMENT_SIGNAL.value:
        errors.append(f"{where}.signal_type: target must be PROCUREMENT_SIGNAL, got {signal_type}")
    if not target and signal_type == SignalType.PROCUREMENT_SIGNAL.value:
        errors.append(f"{where}.signal_type: PROCUREMENT_SIGNAL is only allowed as the target, not in signals[] "
                      "(the cohort report takes the earliest PROCUREMENT_SIGNAL as the downstream target)")
    _text(sig, "title", where, errors)
    if target:
        _text(sig, "target_description", where, errors)
    observed = _parse_time(sig.get("observed_at"), f"{where}.observed_at", errors)
    if observed is not None and observed > ctx.now:
        errors.append(f"{where}.observed_at: {sig['observed_at']} is in the future")
    confidence = _enum(sig, "availability_confidence", CONFIDENCES, where, errors) or ""
    _check_evidence(sig.get("availability_evidence"), confidence, f"{where}.availability_evidence", errors)
    if not isinstance(sig.get("claims"), dict):
        errors.append(f"{where}.claims: must be an object")

    url = sig.get("source_url")
    if not isinstance(url, str) or urlparse(url).scheme not in {"http", "https"} or not urlparse(url).netloc:
        errors.append(f"{where}.source_url: must be an http(s) URL, got {url!r}")
    else:
        report.urls.add(url)
        evidence = sig.get("availability_evidence")
        if (isinstance(evidence, dict) and evidence.get("kind") == "wayback_cdx"
                and not WAYBACK_SNAPSHOT.match(url)):
            warnings.append(f"{where}: Wayback proves the URL existed, not that this text did; capture the "
                            "snapshot (web.archive.org/web/<timestamp>id_/...) or treat as upper bound")
    sha = sig.get("source_sha256")
    if not isinstance(sha, str) or not SHA256_HEX.match(sha):
        errors.append(f"{where}.source_sha256: must be 64 hex characters")
    capture_path = _text(sig, "capture_path", where, errors)
    capture_id = _text(sig, "capture_id", where, errors)

    capture: PublicCapture | None = None
    if capture_path is not None:
        loaded = ctx.capture(capture_path, vertical)
        if isinstance(loaded, str):
            errors.append(f"{where}: {loaded}")
        else:
            capture = loaded
            if isinstance(sha, str) and SHA256_HEX.match(sha) and capture.content_sha256 != sha.lower():
                errors.append(f"{where}.source_sha256: {sha} != capture content_sha256 {capture.content_sha256}")
            if capture_id is not None and capture.capture_id != capture_id:
                errors.append(f"{where}.capture_id: {capture_id!r} != capture file capture_id {capture.capture_id!r}")
            if isinstance(url, str) and capture.source_url != url:
                errors.append(f"{where}.source_url: {url} != capture source_url {capture.source_url}")
            if observed is not None and observed > capture.captured_at:
                errors.append(f"{where}.observed_at: {sig['observed_at']} is after the capture's captured_at "
                              f"{capture.captured_at.isoformat()}")
    _check_quote(sig.get("source_quote"), capture, f"{where}.source_quote", errors, warnings)
    _check_claims(sig, where, warnings)
    return Checked(signal_id or "", observed, confidence, capture)


def _check_evidence(evidence: Any, confidence: str, where: str, errors: list[str]) -> None:
    if not isinstance(evidence, dict):
        errors.append(f"{where}: must be an object")
        return
    _exact_keys(evidence, EVIDENCE_KEYS, where, errors)
    kind = _enum(evidence, "kind", EVIDENCE_KINDS, where, errors)
    cited = confidence == "PROOF_CITED"
    url = _text(evidence, "url", where, errors, empty_ok=not cited)
    _text(evidence, "note", where, errors, empty_ok=not cited)
    if cited:
        if kind in UNPROVEN_KINDS:
            errors.append(f"{where}.kind: PROOF_CITED cannot rest on kind {kind}; use PRINTED_DATE_ONLY or UNKNOWN")
        if url is not None and urlparse(url).scheme not in {"http", "https"}:
            errors.append(f"{where}.url: PROOF_CITED requires an http(s) url to the proof")
    elif confidence in {"PRINTED_DATE_ONLY", "UNKNOWN"} and kind is not None and kind not in UNPROVEN_KINDS:
        errors.append(f"{where}.kind: {confidence} must use kind printed_date or other, not {kind}; "
                      "if the date is provable, use PROOF_CITED")


def _check_lead_time(lead: Any, status: str, signals: dict[str, Checked], target: Checked | None,
                     errors: list[str]) -> str:
    where = "lead_time"
    if not isinstance(lead, dict):
        errors.append(f"{where}: must be an object")
        return ""
    _exact_keys(lead, LEAD_KEYS, where, errors)
    basis = _enum(lead, "basis", BASES, where, errors) or ""
    _text(lead, "note", where, errors, empty_ok=True)
    days = lead.get("days")
    if days is not None and (isinstance(days, bool) or not isinstance(days, int | float) or not math.isfinite(days)):
        errors.append(f"{where}.days: must be a finite number or null")
        days = None
    earliest_id = lead.get("earliest_signal_id")
    earliest: Checked | None = None
    if earliest_id is not None:
        if not isinstance(earliest_id, str) or earliest_id not in signals:
            errors.append(f"{where}.earliest_signal_id: {earliest_id!r} is not a signal_id in signals")
        else:
            earliest = signals[earliest_id]
    dated = [item for item in signals.values() if item.observed_at is not None]
    if earliest is not None and earliest.observed_at is not None and dated:
        first = min(item.observed_at for item in dated if item.observed_at is not None)
        if earliest.observed_at > first:
            errors.append(f"{where}.earliest_signal_id: {earliest_id} is not the earliest signal "
                          f"(observed_at {first} exists)")

    if status == "INCOMPLETE":
        if days is not None or basis != "UNVERIFIED":
            errors.append(f"{where}: INCOMPLETE dossiers must have days null and basis UNVERIFIED")
        return basis
    if target is None:
        if days is not None or basis != "UNVERIFIED":
            errors.append(f"{where}: target is null, so days must be null and basis UNVERIFIED")
        return basis
    provable = (earliest is not None and earliest.confidence == "PROOF_CITED"
                and target.confidence == "PROOF_CITED"
                and earliest.observed_at is not None and target.observed_at is not None)
    if provable:
        expected = (target.observed_at - earliest.observed_at).total_seconds() / 86400  # type: ignore[operator]
        if basis != "PROOF_CITED_TIMESTAMPS":
            errors.append(f"{where}.basis: earliest signal and target are both PROOF_CITED, "
                          "expected PROOF_CITED_TIMESTAMPS")
        if days is None or abs(days - expected) > TOLERANCE_DAYS:
            errors.append(f"{where}.days: {days!r} does not match target - earliest = {expected:.4f} days")
    elif days is not None or basis != "UNVERIFIED":
        errors.append(f"{where}: earliest signal and target are not both PROOF_CITED, "
                      "so days must be null and basis UNVERIFIED")
    return basis


def _check_buyer_path(path: Any, checked: dict[str, Checked], errors: list[str], warnings: list[str]) -> None:
    if not isinstance(path, list):
        errors.append("buyer_path: must be a list")
        return
    for index, entry in enumerate(path):
        where = f"buyer_path[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: must be an object")
            continue
        _exact_keys(entry, BUYER_KEYS, where, errors)
        organization = _text(entry, "organization", where, errors)
        _enum(entry, "role", ROLES, where, errors)
        evidence_id = entry.get("evidence_signal_id")
        source = checked.get(evidence_id) if isinstance(evidence_id, str) else None
        if source is None:
            errors.append(f"{where}.evidence_signal_id: {evidence_id!r} is not a signal or target signal_id")
            continue
        quote = entry.get("quote")
        _check_quote(quote, source.capture, f"{where}.quote", errors, warnings)
        if organization is not None and isinstance(quote, str):
            words = [word for word in re.findall(r"[A-Za-z]{4,}", organization)]
            if words and not any(word.casefold() in quote.casefold() for word in words):
                warnings.append(f"{where}: none of the organization's words ({', '.join(words)}) appears in its quote")


def _check_target_fit(raw: dict[str, Any], has_target: bool, errors: list[str], warnings: list[str]) -> None:
    present = "target_fit" in raw or "target_fit_note" in raw
    if not has_target and not present:
        return
    if has_target or "target_fit" in raw:
        fit = _enum(raw, "target_fit", TARGET_FITS, "dossier", errors)
        if fit in WEAK_TARGET_FITS:
            warnings.append(f"target_fit {fit}: reviewer: consider target null (not a rental/bridge/supply event)")
    if has_target or "target_fit_note" in raw:
        note = raw.get("target_fit_note")
        if not isinstance(note, str) or len(note.strip()) < MIN_FIT_NOTE:
            errors.append(f"dossier.target_fit_note: must be a string of at least {MIN_FIT_NOTE} characters")


def validate_dossier(path: Path, raw: Any, ctx: Context) -> Report:
    report = Report(path=str(path))
    errors, warnings = report.errors, report.warnings
    if not isinstance(raw, dict):
        errors.append("dossier must be a JSON object")
        return report
    _scan_status_claims(raw, "$", errors)
    _exact_keys(raw, TOP_KEYS, "dossier", errors, TOP_OPTIONAL)
    if raw.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version: expected {SCHEMA_VERSION!r}, got {raw.get('schema_version')!r}")
    status = _enum(raw, "status", STATUSES, "dossier", errors) or ""
    vertical = _enum(raw, "vertical", VERTICALS, "dossier", errors) or ""
    report.status, report.vertical = status, vertical
    project_id = raw.get("project_id")
    if not isinstance(project_id, str) or not PROJECT_ID.match(project_id):
        errors.append(f"project_id: {project_id!r} must match {PROJECT_ID.pattern}")
    else:
        report.project_id = project_id
        if path.stem != project_id:
            errors.append(f"project_id {project_id!r} does not match file name {path.name!r}")
    for key in ("project_name", "location", "owner_or_developer", "selection_note", "created_by"):
        _text(raw, key, "dossier", errors)
    created = _parse_time(raw.get("created_at"), "created_at", errors)
    if created is not None and created > ctx.now:
        errors.append(f"created_at: {raw['created_at']} is in the future")
    for key in ("blockers", "reviewer_checklist", "later_procurement_events"):
        value = raw.get(key)
        if key not in raw and key == "later_procurement_events":
            continue
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"{key}: must be a list of strings")

    signals_raw = raw.get("signals")
    checked: dict[str, Checked] = {}
    signals: dict[str, Checked] = {}
    if not isinstance(signals_raw, list):
        errors.append("signals: must be a list")
        signals_raw = []
    report.signals = len(signals_raw)
    if status == "PROPOSED_UNREVIEWED" and len(signals_raw) < 2:
        errors.append(f"signals: PROPOSED_UNREVIEWED requires at least 2 signals, got {len(signals_raw)}")
    for index, sig in enumerate(signals_raw):
        item = _check_signal(sig, f"signals[{index}]", vertical, ctx, errors, warnings, report, target=False)
        if item is not None and item.signal_id:
            if item.signal_id in checked:
                errors.append(f"signals[{index}]: duplicate signal_id {item.signal_id!r}")
            checked[item.signal_id] = signals[item.signal_id] = item

    target_raw = raw.get("target")
    target: Checked | None = None
    report.has_target = target_raw is not None
    if target_raw is not None:
        target = _check_signal(target_raw, "target", vertical, ctx, errors, warnings, report, target=True)
        if target is not None and target.signal_id:
            if target.signal_id in checked:
                errors.append(f"target: signal_id {target.signal_id!r} duplicates a signal in signals")
            checked[target.signal_id] = target
        if target is not None and target.observed_at is not None:
            for item in signals.values():
                if item.observed_at is not None and item.observed_at > target.observed_at:
                    errors.append(f"signal {item.signal_id} observed_at {item.observed_at.isoformat()} is after "
                                  f"target observed_at {target.observed_at.isoformat()}")
    elif status == "PROPOSED_UNREVIEWED":
        warnings.append("no target: this case stays unresolved (not negative) until a target is found")
    _check_target_fit(raw, target_raw is not None, errors, warnings)

    _check_buyer_path(raw.get("buyer_path"), checked, errors, warnings)
    report.basis = _check_lead_time(raw.get("lead_time"), status, signals,
                                    target if target_raw is not None else None, errors)
    if len(report.urls) == 1:
        warnings.append("single-source dossier: every signal cites the same source_url")
    return report


def collect(root: Path) -> list[Path]:
    return sorted(root.glob("*/dossiers/*.json"))


def run(root: Path, repo_root: Path = ROOT, now: datetime | None = None) -> list[Report]:
    ctx = Context(repo_root, now or datetime.now(UTC))
    reports: list[Report] = []
    seen: dict[str, Path] = {}
    for path in collect(root):
        try:
            raw = _loads_strict(path.read_text(encoding="utf-8"))
            report = validate_dossier(path, raw, ctx)
            if report.vertical and path.parent.parent.name != report.vertical:
                report.errors.append(
                    f"vertical {report.vertical!r} does not match directory {path.parent.parent.name!r}")
        except RecursionError:
            report = Report(path=str(path), errors=["dossier JSON is nested too deeply (RecursionError)"])
        except (OSError, ValueError) as exc:
            report = Report(path=str(path), errors=[f"cannot read dossier JSON: {exc}"])
        if report.project_id:
            if report.project_id in seen:
                report.errors.append(f"duplicate project_id {report.project_id!r} (also in {seen[report.project_id]})")
            seen.setdefault(report.project_id, path)
        reports.append(report)
    users: dict[str, set[str]] = {}
    for report in reports:
        for url in report.urls:
            users.setdefault(url, set()).add(report.project_id or report.path)
    for report in reports:
        for url in sorted(report.urls):
            others = users[url] - {report.project_id or report.path}
            if others:
                report.warnings.append(f"source_url {url} is also used by {', '.join(sorted(others))}")
    return reports


def _totals(reports: list[Report]) -> dict[str, int]:
    return {
        "dossiers": len(reports), "passed": sum(1 for r in reports if not r.errors),
        "failed": sum(1 for r in reports if r.errors), "errors": sum(len(r.errors) for r in reports),
        "warnings": sum(len(r.warnings) for r in reports),
    }


def render_text(reports: list[Report]) -> str:
    lines: list[str] = []
    for report in reports:
        lines.append(f"{'FAIL' if report.errors else 'PASS'} {report.path}")
        lines += [f"  ERROR: {message}" for message in report.errors]
        lines += [f"  WARN: {message}" for message in report.warnings]
    header = ("project_id", "vertical", "status", "signals", "target", "lead-time basis", "errors")
    rows = [(r.project_id or "?", r.vertical or "?", r.status or "?", str(r.signals), "yes" if r.has_target else "no",
             r.basis or "?", str(len(r.errors))) for r in reports]
    widths = [max(len(header[i]), *(len(row[i]) for row in rows)) if rows else len(header[i]) for i in range(7)]
    lines += ["", " | ".join(h.ljust(w) for h, w in zip(header, widths, strict=True))]
    lines.append("-+-".join("-" * w for w in widths))
    lines += [" | ".join(c.ljust(w) for c, w in zip(row, widths, strict=True)) for row in rows]
    totals = _totals(reports)
    lines.append("")
    lines.append("totals: " + ", ".join(f"{key}={value}" for key, value in totals.items()))
    if not reports:
        lines.append("no dossiers found")
    return "\n".join(lines)


def main(argv: list[str] | None = None, *, repo_root: Path = ROOT, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None,
                        help=f"directory holding <vertical>/dossiers/*.json (default {DEFAULT_ROOT}; an explicit "
                             "--root with no dossiers is an error)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)
    root = Path(args.root or DEFAULT_ROOT)
    if not root.is_absolute():
        root = repo_root / root
    if not root.is_dir():
        print(f"error: root {root} is not a directory", file=sys.stderr)
        return 2
    reports = run(root, repo_root, now)
    totals = _totals(reports)
    if args.json:
        print(json.dumps({"ok": totals["errors"] == 0, "totals": totals, "dossiers": [r.as_dict() for r in reports]},
                         indent=2, sort_keys=True))
    else:
        print(render_text(reports))
    if not reports and args.root is not None:
        print(f"error: no dossiers found under explicit --root {root}", file=sys.stderr)
        return 2
    return 0 if totals["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
