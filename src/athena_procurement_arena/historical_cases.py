"""Source-bound historical cases over the existing scenario/replay engine."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Any

from athena_arena.contracts import canonical_hash

from .foundation import Scenario, validate_scenario
from .policies import PreRfpBaselineV1
from .public_capture import load_capture
from .scenario_dsl import ScenarioDsl
from .world import TemporalWorld

UNKNOWN = "UNKNOWN"
_CASE_SCHEMA = "trailforge-pre-rfp-case-v1"
_OUTCOMES = {
    "RELEVANT_PROCUREMENT_OBSERVED", "PRIVATE_BUYING_EVENT_VERIFIED", "CANCELED", "DELAYED",
    "SUPPLY_RESOLVED", "INCOMPATIBLE_SOLUTION", "AWARDED_BEFORE_DETECTION",
    "GENERATION_NOT_IN_SCOPE", "NO_OUTCOME_OBSERVED", "UNKNOWN",
}
_BUYER_QUALITIES = {
    "UNKNOWN", "ORGANIZATION_IDENTIFIED", "RESPONSIBLE_ROLE_IDENTIFIED",
    "PROJECT_RESPONSIBILITY_SUPPORTED", "BUYING_RESPONSIBILITY_SUPPORTED",
}
_BUYER_ROLES = {
    "OWNER", "DEVELOPER", "UTILITY", "EPC", "GC", "ELECTRICAL_CONTRACTOR",
    "COMMISSIONING_CONTRACTOR", "FACILITY_OPERATOR", "PROCUREMENT_ORGANIZATION",
    "OWNER_OR_PROCUREMENT_ORGANIZATION", "OTHER", "UNKNOWN",
}


def _timestamp(value: str, field: str) -> datetime | None:
    if value == UNKNOWN:
        return None
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone or be UNKNOWN")
    return result


@dataclass(frozen=True)
class EvidenceSourceRef:
    evidence_id: str
    capture_path: str
    capture_id: str
    capture_hash: str
    content_sha256: str
    source_url: str
    source_quote: str
    reviewed_claims: dict[str, Any]
    event_date: str
    document_date: str
    verified_available_at: str
    observed_at: str
    replay_included: bool = True
    extra_fields: dict[str, Any] | None = None


@dataclass(frozen=True)
class HistoricalCase:
    case_id: str
    procurement_family_id: str
    project_identity: str
    location: str
    facility_type: str
    power_activity: str
    purchase_type: str
    outcome: str
    known_buying_event: str
    buying_event_date: str
    conventional_milestone: str
    conventional_milestone_at: str
    conventional_milestone_evidence_id: str | None
    scenario_path: str
    holdout_group: str
    buyer_path: tuple[dict[str, str], ...]
    evidence_sources: tuple[EvidenceSourceRef, ...]
    extra_fields: dict[str, Any] = field(default_factory=dict)

    @property
    def case_hash(self) -> str:
        return canonical_hash({item.name: getattr(self, item.name) for item in fields(self)})


def load_case(path: str | Path) -> tuple[HistoricalCase, Scenario]:
    """Load a case and verify every claim/event against its immutable capture."""
    manifest_path = Path(path).resolve(strict=True)
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != _CASE_SCHEMA:
        raise ValueError("unsupported historical case schema_version")
    ref_fields = set(EvidenceSourceRef.__dataclass_fields__) - {"extra_fields"}
    sources = tuple(EvidenceSourceRef(**{**{key: value for key, value in item.items() if key in ref_fields},
                                      "extra_fields": {key: value for key, value in item.items()
                                                       if key not in ref_fields}})
                    for item in raw.get("evidence_sources", ()))
    case = HistoricalCase(
        case_id=raw["case_id"], procurement_family_id=raw["procurement_family_id"],
        project_identity=raw["project_identity"], location=raw.get("location", UNKNOWN),
        facility_type=raw["facility_type"],
        power_activity=raw["power_activity"], purchase_type=raw["purchase_type"],
        outcome=raw["outcome"], known_buying_event=raw["known_buying_event"],
        buying_event_date=raw["buying_event_date"],
        conventional_milestone=raw["conventional_milestone"],
        conventional_milestone_at=raw["conventional_milestone_at"],
        conventional_milestone_evidence_id=raw.get("conventional_milestone_evidence_id"),
        scenario_path=raw["scenario_path"], holdout_group=raw.get("holdout_group", "UNKNOWN"),
        buyer_path=tuple(dict(item) for item in raw.get("buyer_path", ())),
        evidence_sources=sources,
        extra_fields={key: value for key, value in raw.items()
                      if key not in {"schema_version", "case_id", "procurement_family_id", "project_identity", "location",
                                     "facility_type", "power_activity", "purchase_type", "outcome",
                                     "known_buying_event", "buying_event_date", "conventional_milestone",
                                     "conventional_milestone_at", "conventional_milestone_evidence_id",
                                     "scenario_path", "holdout_group", "buyer_path", "evidence_sources"}},
    )
    required = (case.case_id, case.procurement_family_id, case.project_identity, case.facility_type,
                case.power_activity, case.purchase_type, case.outcome, case.known_buying_event,
                case.conventional_milestone, case.scenario_path)
    if any(not isinstance(value, str) or not value.strip() for value in required):
        raise ValueError("case identity and classification fields are required; use UNKNOWN for missing facts")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", case.case_id):
        raise ValueError("case_id must be a safe path component of at most 64 characters")
    if case.outcome not in _OUTCOMES:
        raise ValueError(f"unsupported case outcome: {case.outcome}")
    _timestamp(case.buying_event_date, "buying_event_date")
    _timestamp(case.conventional_milestone_at, "conventional_milestone_at")
    scenario_path = (manifest_path.parent / case.scenario_path).resolve(strict=True)
    if scenario_path.parent != manifest_path.parent:
        raise ValueError("scenario_path must remain inside its case directory")
    scenario = ScenarioDsl.loads(scenario_path.read_text(encoding="utf-8"))
    validate_scenario(scenario)
    if scenario.scenario_id != case.case_id:
        raise ValueError("scenario_id must match case_id")
    if scenario.truth.procurement_episode_id != case.procurement_family_id:
        raise ValueError("scenario truth procurement identity must match procurement_family_id")
    if any(event.lineage_family != case.procurement_family_id for event in scenario.evidence):
        raise ValueError("scenario evidence lineage_family must match procurement_family_id")
    by_id = {event.evidence_id: event for event in scenario.evidence}
    if len({ref.evidence_id for ref in sources}) != len(sources):
        raise ValueError("case evidence_sources contains duplicate evidence IDs")
    for ref in sources:
        _verify_source_ref(manifest_path.parent, ref, by_id)
    if set(by_id) != {ref.evidence_id for ref in sources if ref.replay_included and _fully_dated(ref)}:
        raise ValueError("scenario evidence must contain exactly the replay-included fully timestamped refs")
    _verify_buyer_path(case)
    milestone_at = _timestamp(case.conventional_milestone_at, "conventional_milestone_at")
    if milestone_at is not None:
        milestone_evidence = by_id.get(case.conventional_milestone_evidence_id or "")
        if milestone_evidence is None or milestone_evidence.event_date != milestone_at:
            raise ValueError("a dated conventional milestone requires matching replay evidence")
    return case, scenario


def _fully_dated(ref: EvidenceSourceRef) -> bool:
    values = (ref.event_date, ref.document_date, ref.verified_available_at, ref.observed_at)
    return all(value != UNKNOWN for value in values)


def _verify_source_ref(root: Path, ref: EvidenceSourceRef, events: dict[str, Any]) -> None:
    # Validate every supplied timestamp before the non-replay/partial-evidence
    # branch below. UNKNOWN remains explicit and is never inferred from capture data.
    for field_name in ("event_date", "document_date", "verified_available_at", "observed_at"):
        _timestamp(getattr(ref, field_name), f"{field_name} ({ref.evidence_id})")
    capture_path = (root / ref.capture_path).resolve(strict=True)
    corpus_root = root.parent.parent.resolve()
    if not capture_path.is_relative_to(corpus_root):
        raise ValueError(f"capture path leaves the pre-RFP corpus: {ref.evidence_id}")
    capture = load_capture(capture_path)
    if (capture.capture_id != ref.capture_id or capture.capture_hash != ref.capture_hash
            or capture.content_sha256 != ref.content_sha256 or capture.source_url != ref.source_url):
        raise ValueError(f"capture identity/hash mismatch for evidence {ref.evidence_id}")
    if not ref.source_quote or ref.source_quote not in capture.content:
        raise ValueError(f"source quote is absent from capture for evidence {ref.evidence_id}")
    if ref.verified_available_at != UNKNOWN:
        available_at = _timestamp(ref.verified_available_at, "verified_available_at")
        if available_at is not None and available_at < capture.captured_at:
            proof_path_value = (ref.extra_fields or {}).get("availability_proof_capture_path")
            proof_hash = (ref.extra_fields or {}).get("availability_proof_capture_hash")
            if not proof_path_value or not proof_hash:
                raise ValueError(f"pre-capture availability needs a separately bound historical proof: {ref.evidence_id}")
            proof_path = (root / proof_path_value).resolve(strict=True)
            if not proof_path.is_relative_to(corpus_root):
                raise ValueError(f"availability proof leaves the pre-RFP corpus: {ref.evidence_id}")
            proof = load_capture(proof_path)
            if (proof.capture_hash != proof_hash or proof.source_url != ref.source_url
                    or proof.content_sha256 != ref.content_sha256 or proof.captured_at > available_at):
                raise ValueError(f"historical availability proof does not bind the exact earlier version: {ref.evidence_id}")
    event = events.get(ref.evidence_id)
    if not ref.replay_included or not _fully_dated(ref):
        if event is not None:
            raise ValueError(f"non-replay evidence must be excluded from scenario: {ref.evidence_id}")
        return
    if event is None:
        raise ValueError(f"fully dated evidence is missing from scenario: {ref.evidence_id}")
    expected_dates = (ref.event_date, ref.document_date, ref.verified_available_at, ref.observed_at)
    actual_dates = tuple(getattr(event, key).isoformat() for key in
                         ("event_date", "document_date", "verified_available_at", "observed_at"))
    if (event.source_id != ref.capture_id or event.source_version != ref.content_sha256
            or dict(event.claims) != ref.reviewed_claims or actual_dates != expected_dates):
        raise ValueError(f"scenario event does not match reviewed capture ref: {ref.evidence_id}")
    if ref.source_quote not in event.source_spans:
        raise ValueError(f"scenario event is missing the reviewed source quote: {ref.evidence_id}")
    if ref.extra_fields and ref.extra_fields.get("observation_kind") == "CURRENT_SOURCE_OBSERVATION":
        if ref.extra_fields.get("availability_basis") != "CAPTURE_TIME_ONLY":
            raise ValueError("current source observation must declare capture-time-only availability")
        if not isinstance(ref.extra_fields.get("date_semantics"), str) or not ref.extra_fields["date_semantics"].strip():
            raise ValueError("current source observation must explain its event/document date semantics")
        capture = load_capture((root / ref.capture_path).resolve(strict=True))
        if any(value != capture.captured_at.isoformat() for value in expected_dates[2:]):
            raise ValueError("current source observation availability and observation times must equal capture time")


def _verify_buyer_path(case: HistoricalCase) -> None:
    evidence_by_id = {item.evidence_id: item for item in case.evidence_sources}
    for item in case.buyer_path:
        required = {"organization", "role", "quality", "evidence_id"}
        if not required.issubset(item):
            raise ValueError("buyer_path records require organization, role, quality, and evidence_id")
        if any(not isinstance(item[key], str) for key in required):
            raise ValueError("buyer_path fields must be strings")
        if item["quality"] not in _BUYER_QUALITIES:
            raise ValueError(f"unsupported buyer-path quality: {item['quality']}")
        if item["role"] not in _BUYER_ROLES:
            raise ValueError(f"unsupported buyer-path role: {item['role']}")
        if item["evidence_id"] not in evidence_by_id:
            raise ValueError("buyer_path evidence_id must reference retained case evidence")
        organization = item["organization"].strip()
        if item["quality"] != "UNKNOWN" and (not organization or organization.upper() == "UNKNOWN"):
            raise ValueError("identified buyer-path quality requires an identified organization")
        if item["quality"] != "UNKNOWN":
            claims = evidence_by_id[item["evidence_id"]].reviewed_claims
            if claims.get("buyer_organization") != organization:
                raise ValueError("buyer_path organization must match the reviewed evidence claim")


def validate_family_splits(cases: tuple[HistoricalCase, ...] | list[HistoricalCase]) -> None:
    """Keep known project and procurement identities within one cohort split."""
    by_family: dict[str, set[str]] = {}
    by_project: dict[str, set[str]] = {}
    by_capture: dict[str, set[str]] = {}
    by_content: dict[str, set[str]] = {}
    for case in cases:
        by_family.setdefault(case.procurement_family_id, set()).add(case.holdout_group)
        if case.project_identity.strip().upper() != UNKNOWN:
            by_project.setdefault(case.project_identity.strip(), set()).add(case.holdout_group)
        for ref in case.evidence_sources:
            by_capture.setdefault(ref.capture_hash, set()).add(case.holdout_group)
            by_content.setdefault(ref.content_sha256, set()).add(case.holdout_group)
    for label, groups in (("project identity", by_project), ("procurement family", by_family), ("capture hash", by_capture),
                          ("content hash", by_content)):
        split = next((identity for identity, splits in groups.items() if len(splits) > 1), None)
        if split:
            raise ValueError(f"{label} split across cohort groups: {split}")


def replay_case(path: str | Path, *, mode: str, policy: Any, experiment_dir: str | Path) -> dict[str, Any]:
    """Persist the existing comparator and hash-bind a pre-RFP baseline replay."""
    from .runner import create_experiment, verify_experiment

    if mode not in {"BACKTRACE", "DISCOVERY"}:
        raise ValueError("mode must be BACKTRACE or DISCOVERY")
    case, scenario = load_case(path)
    # Historical backtraces and retained acquisition assertions do not establish
    # prospective, independently evaluated discovery performance in this slice.
    discovery_credit = False
    scenario_text = ScenarioDsl.dumps(scenario)
    if getattr(policy, "policy_id", None) != "BASELINE_A":
        raise ValueError("the stored comparator must be existing BASELINE_A")
    manifest = create_experiment(
        scenario_text, str(Path(path).resolve()), experiment_dir, policy,
        policy_id=getattr(policy, "policy_id", ""),
    )
    checked, artifacts = verify_experiment(experiment_dir)
    if checked["manifest_hash"] != manifest["manifest_hash"]:
        raise ValueError("persisted experiment verification failed")
    records = artifacts["decisions.json"]["records"]
    baseline_actionable = [item for item in records if item.get("action") in {"RESEARCH", "PREPARE", "BID_REVIEW"}]
    baseline_first = baseline_actionable[0] if baseline_actionable else None

    pre_policy = PreRfpBaselineV1()
    pre_world = TemporalWorld(scenario, pre_policy.policy_id, pre_policy)
    pre_world.run()
    pre_records = pre_world.ledger.records
    pre_actionable = [item for item in pre_records if item.action in {"RESEARCH", "PREPARE", "BID_REVIEW"}]
    first = pre_actionable[0] if pre_actionable else None
    milestone = _timestamp(case.conventional_milestone_at, "conventional_milestone_at")
    first_at = first.simulation_time if first else None
    lead = (milestone - first_at).total_seconds() if milestone and first_at else None
    milestone_supported = milestone is not None and case.conventional_milestone_evidence_id is not None
    decision_rows = [{
        "simulation_time": item.simulation_time.isoformat(), "action": item.action,
        "visible_evidence_ids": list(item.visible_evidence_ids), "forecast": dict(item.forecast),
        "record_hash": item.record_hash,
    } for item in pre_records]
    decision_hash = canonical_hash(decision_rows)
    visible_at_first = set(first.visible_evidence_ids) if first else set()
    buyer_path_at_first = [item for item in case.buyer_path if item["evidence_id"] in visible_at_first]
    return {
        "schema_version": "trailforge-pre-rfp-case-replay-v1",
        "case_id": case.case_id, "case_hash": case.case_hash,
        "procurement_family_id": case.procurement_family_id,
        "mode": mode, "discovery_credit": discovery_credit,
        "discovery_credit_reason": ("SLICE_A_DOES_NOT_AWARD_DISCOVERY_CREDIT" if mode == "DISCOVERY" else
                                     "BACKTRACE_HAS_NO_DISCOVERY_CREDIT"),
        "policy_id": artifacts["config.json"]["policy_id"],
        "pre_rfp_policy_id": pre_policy.policy_id,
        "scenario_hash": checked["scenario_hash"], "experiment_manifest_hash": checked["manifest_hash"],
        "experiment_dir": str(Path(experiment_dir).resolve()),
        "decision_count": len(records), "ledger_verified": artifacts["decisions.json"]["ledger_verified"],
        "baseline_first_action": baseline_first["action"] if baseline_first else None,
        "baseline_first_surface_at": baseline_first["simulation_time"] if baseline_first else None,
        "pre_rfp_first_action": first.action if first else None,
        "pre_rfp_first_surface_at": first.simulation_time.isoformat() if first else None,
        "pre_rfp_decision_count": len(pre_records), "pre_rfp_ledger_verified": pre_world.ledger.verify(),
        "pre_rfp_decision_hash": decision_hash, "pre_rfp_decisions": decision_rows,
        "conventional_milestone_at": case.conventional_milestone_at,
        "historical_lead_seconds": lead if milestone_supported else None,
        "lead_status": ("SUPPORTED" if lead is not None and lead >= 0 and milestone_supported else
                        "NO_EARLY_ADVANTAGE" if lead is not None and milestone_supported else
                        "NO_SURFACE" if milestone_supported else "UNKNOWN"),
        "historical_replay_credit": False,
        "historical_replay_credit_reason": "CURRENT_CAPTURE_OBSERVATIONS_ONLY" if (
            any(ref.replay_included for ref in case.evidence_sources) and all(
                ref.extra_fields and ref.extra_fields.get("observation_kind") == "CURRENT_SOURCE_OBSERVATION"
                for ref in case.evidence_sources if ref.replay_included
            )) else "NO_INDEPENDENT_DISCOVERY_VALIDATION",
        "reviewed_buyer_path": list(case.buyer_path),
        "buyer_path_at_first_surface": buyer_path_at_first,
        "buyer_path_at_first_surface_status": (
            "SUPPORTED" if any(item["quality"] != "UNKNOWN" for item in buyer_path_at_first) else
            "UNKNOWN" if first else "NO_SURFACE"),
        "outcome": case.outcome,
        "unknown_availability_count": sum(not _fully_dated(ref) for ref in case.evidence_sources),
    }


def write_replay_result(result: dict[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
