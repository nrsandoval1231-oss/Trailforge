from __future__ import annotations

import json
from datetime import datetime

import pytest

from athena_procurement_arena.foundation import EvidenceEvent, GroundTruth, Scenario
from athena_procurement_arena.historical_cases import load_case, replay_case, validate_family_splits
from athena_procurement_arena.policies import BaselineA, PreRfpBaselineV1
from athena_procurement_arena.public_capture import capture_markdown, write_capture
from athena_procurement_arena.scenario_dsl import ScenarioDsl
from athena_procurement_arena.world import TemporalWorld


def _iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _case_bundle(root, *, split="DEVELOPMENT", quotes_supported=True):
    case_dir = root / "case-1"
    evidence_dir = case_dir / "evidence"
    evidence_dir.mkdir(parents=True)
    captured_at = datetime.fromisoformat("2026-10-02T13:54:25.267650+00:00")
    quote = "The City will provide temporary generation for construction continuity."
    capture = capture_markdown("https://example.gov/project", quote, capture_id="capture-1",
                               captured_by="reviewer", captured_at=captured_at)
    write_capture(capture, evidence_dir / "capture.json")
    claims = {"project_specific": True, "generation_need_supported": True,
              "need_reason": "construction continuity", "buyer_organization": "Example City",
              "required_mw": None}
    event = EvidenceEvent(
        evidence_id="capture-observation-1", source_id=capture.capture_id,
        event_date=captured_at, document_date=captured_at, verified_available_at=captured_at,
        observed_at=captured_at, claims=claims, source_version=capture.content_sha256,
        lineage_family="family-1", source_spans=(quote,), permission_scope="PUBLIC",
    )
    scenario = Scenario("case-1", "1", 1, (captured_at,), (event,),
                        GroundTruth("family-1", "NO_OUTCOME_OBSERVED"))
    (case_dir / "scenario.json").write_text(ScenarioDsl.dumps(scenario), encoding="utf-8")
    raw_source = {
        "evidence_id": "capture-observation-1", "capture_path": "evidence/capture.json",
        "capture_id": capture.capture_id, "capture_hash": capture.capture_hash,
        "content_sha256": capture.content_sha256, "source_url": capture.source_url,
        "source_quote": quote, "reviewed_claims": claims,
        "event_date": captured_at.isoformat(), "document_date": captured_at.isoformat(),
        "verified_available_at": captured_at.isoformat(), "observed_at": captured_at.isoformat(),
        "replay_included": True, "observation_kind": "CURRENT_SOURCE_OBSERVATION",
        "availability_basis": "CAPTURE_TIME_ONLY",
        "date_semantics": "Capture-time observation of a source statement; no earlier availability asserted.",
    }
    if not quotes_supported:
        raw_source["source_quote"] = "unsupported quote"
    # Earlier historical facts are retained without manufacturing a chronology.
    historical = {**raw_source, "evidence_id": "historical-claim-1", "event_date": "UNKNOWN",
                  "document_date": "UNKNOWN", "verified_available_at": "UNKNOWN", "observed_at": "UNKNOWN",
                  "replay_included": False, "reported_event_date": "2024-01-01"}
    case = {
        "schema_version": "trailforge-pre-rfp-case-v1", "case_id": "case-1",
        "procurement_family_id": "family-1", "project_identity": "Example City Facility",
        "facility_type": "industrial", "power_activity": "construction", "purchase_type": "temporary_power_service",
        "commercial_fit": {"required_mw": "UNKNOWN"}, "outcome": "NO_OUTCOME_OBSERVED",
        "known_buying_event": "UNKNOWN", "buying_event_date": "UNKNOWN",
        "conventional_milestone": "UNKNOWN", "conventional_milestone_at": "UNKNOWN",
        "scenario_path": "scenario.json", "holdout_group": split,
        "buyer_path": [{"organization": "Example City", "role": "OWNER", "quality": "ORGANIZATION_IDENTIFIED",
                        "evidence_id": "capture-observation-1"}],
        "evidence_sources": [historical, raw_source],
    }
    (case_dir / "case.json").write_text(json.dumps(case), encoding="utf-8")
    return case_dir / "case.json", case


def test_pre_rfp_baseline_requires_supported_project_need_reason_and_buyer():
    policy = PreRfpBaselineV1()
    assert policy({"visible_evidence": []})[1] == "IGNORE"
    event = {"evidence_id": "e1", "claims": {
        "project_specific": True, "generation_need_supported": True,
        "need_reason": "phased energization", "buyer_organization": "Owner", "required_mw": None,
    }}
    forecast, action = policy({"visible_evidence": [event]})
    assert action == "RESEARCH"
    assert forecast["power_need_status"] == "UNKNOWN"
    assert forecast["basis_evidence_ids"] == ["e1"]
    assert policy({"visible_evidence": [{"evidence_id": "e2", "claims": {**event["claims"], "awarded": True}}]})[1] == "IGNORE"


@pytest.mark.parametrize("field,value", [
    ("buyer_organization", "UNKNOWN"), ("buyer_organization", "  unknown \t"),
    ("buyer_organization", ""), ("buyer_organization", "   "),
    ("need_reason", "UNKNOWN"), ("need_reason", "\n UnKnOwN "),
    ("need_reason", ""), ("need_reason", "   "),
])
def test_pre_rfp_baseline_never_surfaces_unknown_or_blank_buyer_or_reason(field, value):
    policy = PreRfpBaselineV1()
    claims = {"project_specific": True, "generation_need_supported": True,
              "need_reason": "phased energization", "buyer_organization": "Owner"}
    claims[field] = value
    forecast, action = policy({"visible_evidence": [{"evidence_id": "e1", "claims": claims}]})
    assert action == "IGNORE"
    assert forecast["basis_evidence_ids"] == []


def test_later_available_evidence_cannot_surface_early():
    earlier = _iso("2026-01-01T00:00:00+00:00")
    available = _iso("2026-06-01T00:00:00+00:00")
    quote = "Evidence became available later."
    event = EvidenceEvent("e1", "s1", earlier, earlier, available, available,
                         {"project_specific": True, "generation_need_supported": True,
                          "need_reason": "documented need", "buyer_organization": "Owner"},
                         source_spans=(quote,))
    scenario = Scenario("temporal", "1", 1, (earlier, available), (event,), GroundTruth("p", "UNKNOWN"))
    world = TemporalWorld(scenario, PreRfpBaselineV1.policy_id, PreRfpBaselineV1())
    world.run()
    assert world.ledger.records[0].visible_evidence_ids == ()
    assert world.ledger.records[0].action == "IGNORE"
    assert world.ledger.records[1].visible_evidence_ids == ("e1",)
    assert world.ledger.records[1].action == "RESEARCH"


def test_case_import_binds_immutable_capture_and_unknown_history(tmp_path):
    case_path, _ = _case_bundle(tmp_path)
    case, scenario = load_case(case_path)
    assert case.outcome == "NO_OUTCOME_OBSERVED"
    assert len(scenario.evidence) == 1
    assert case.evidence_sources[1].extra_fields["availability_basis"] == "CAPTURE_TIME_ONLY"
    assert case.evidence_sources[0].extra_fields["reported_event_date"] == "2024-01-01"


def test_case_import_rejects_unbound_quote(tmp_path):
    case_path, _ = _case_bundle(tmp_path, quotes_supported=False)
    with pytest.raises(ValueError, match="quote is absent"):
        load_case(case_path)


def test_case_import_rejects_backdated_availability_without_earlier_version_capture(tmp_path):
    case_path, raw = _case_bundle(tmp_path)
    observation = raw["evidence_sources"][1]
    observation["verified_available_at"] = "2026-10-01T00:00:00+00:00"
    case_path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="pre-capture availability"):
        load_case(case_path)


@pytest.mark.parametrize("identity_field", ["scenario_id", "truth", "lineage_family"])
def test_case_import_rejects_scenario_identity_mismatch(tmp_path, identity_field):
    from dataclasses import replace

    case_path, _ = _case_bundle(tmp_path)
    scenario_path = case_path.parent / "scenario.json"
    scenario = ScenarioDsl.loads(scenario_path.read_text(encoding="utf-8"))
    if identity_field == "scenario_id":
        scenario = replace(scenario, scenario_id="another-case")
    elif identity_field == "truth":
        scenario = replace(scenario, truth=replace(scenario.truth, procurement_episode_id="another-family"))
    else:
        scenario = replace(scenario, evidence=(replace(scenario.evidence[0], lineage_family="another-family"),))
    scenario_path.write_text(ScenarioDsl.dumps(scenario), encoding="utf-8")
    with pytest.raises(ValueError, match="must match"):
        load_case(case_path)


def test_buyer_path_must_match_supported_source_organization(tmp_path):
    case_path, raw = _case_bundle(tmp_path)
    raw["buyer_path"][0]["organization"] = "UNKNOWN"
    case_path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="identified organization"):
        load_case(case_path)


def test_family_cannot_split_across_cohort_groups(tmp_path):
    from dataclasses import replace

    first, data = _case_bundle(tmp_path / "first")
    second, second_data = _case_bundle(tmp_path / "second", split="HOLDOUT")
    second_data["case_id"] = "case-2"
    second_data["procurement_family_id"] = data["procurement_family_id"]
    second.write_text(json.dumps(second_data), encoding="utf-8")
    second_scenario_path = second.parent / "scenario.json"
    second_scenario = ScenarioDsl.loads(second_scenario_path.read_text(encoding="utf-8"))
    second_scenario = ScenarioDsl.dumps(replace(second_scenario, scenario_id="case-2"))
    second_scenario_path.write_text(second_scenario, encoding="utf-8")
    one, _ = load_case(first)
    two, _ = load_case(second)
    with pytest.raises(ValueError, match="family split"):
        validate_family_splits((one, two))


def test_identical_capture_cannot_cross_splits_under_different_family_ids(tmp_path):
    from dataclasses import replace

    first, _ = _case_bundle(tmp_path / "first")
    second, second_data = _case_bundle(tmp_path / "second", split="HOLDOUT")
    second_data["case_id"] = "case-2"
    second_data["procurement_family_id"] = "family-2"
    second.write_text(json.dumps(second_data), encoding="utf-8")
    scenario_path = second.parent / "scenario.json"
    scenario = ScenarioDsl.loads(scenario_path.read_text(encoding="utf-8"))
    event = replace(scenario.evidence[0], lineage_family="family-2")
    scenario = replace(scenario, scenario_id="case-2", evidence=(event,),
                       truth=replace(scenario.truth, procurement_episode_id="family-2"))
    scenario_path.write_text(ScenarioDsl.dumps(scenario), encoding="utf-8")
    one, _ = load_case(first)
    two, _ = load_case(second)
    with pytest.raises(ValueError, match="capture hash split|content hash split"):
        validate_family_splits((one, two))


def test_replay_is_offline_and_never_awards_discovery_credit(tmp_path):
    case_path, _ = _case_bundle(tmp_path)
    result = replay_case(case_path, mode="DISCOVERY", policy=BaselineA(),
                        experiment_dir=tmp_path / "experiments" / "case-1")
    assert result["mode"] == "DISCOVERY"
    assert result["discovery_credit"] is False
    assert result["historical_replay_credit"] is False
    assert result["pre_rfp_first_action"] == "RESEARCH"
    assert result["pre_rfp_first_surface_at"] == "2026-10-02T13:54:25.267650+00:00"
    assert result["lead_status"] == "UNKNOWN"
    assert result["unknown_availability_count"] == 1
    assert result["buyer_path_at_first_surface_status"] == "SUPPORTED"
    assert result["buyer_path_at_first_surface"][0]["organization"] == "Example City"
    assert (tmp_path / "experiments" / "case-1" / "manifest.json").exists()


def test_late_surface_retains_numeric_negative_lead(tmp_path):
    from dataclasses import replace

    case_path, raw = _case_bundle(tmp_path)
    case_dir = case_path.parent
    scenario = ScenarioDsl.loads((case_dir / "scenario.json").read_text(encoding="utf-8"))
    milestone = _iso("2026-10-01T13:54:25.267650+00:00")
    event = replace(scenario.evidence[0], event_date=milestone)
    scenario = replace(scenario, evidence=(event,))
    (case_dir / "scenario.json").write_text(ScenarioDsl.dumps(scenario), encoding="utf-8")
    observation = raw["evidence_sources"][1]
    observation["event_date"] = milestone.isoformat()
    observation["date_semantics"] = "Source describes a prior milestone; availability is capture time only."
    raw["conventional_milestone"] = "Verified project milestone"
    raw["conventional_milestone_at"] = milestone.isoformat()
    raw["conventional_milestone_evidence_id"] = observation["evidence_id"]
    case_path.write_text(json.dumps(raw), encoding="utf-8")
    result = replay_case(case_path, mode="BACKTRACE", policy=BaselineA(),
                         experiment_dir=tmp_path / "experiments" / "case-1")
    assert result["historical_lead_seconds"] == -86400.0
    assert result["lead_status"] == "NO_EARLY_ADVANTAGE"
