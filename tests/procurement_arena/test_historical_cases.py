from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path

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


def test_historical_report_requires_loaded_case_not_caller_claims():
    from athena_procurement_arena.historical_case_report import build_case_report

    with pytest.raises(TypeError, match="HistoricalCase"):
        build_case_report({"case_id": "forged"}, {}, {"ledger_verified": True}, {})


def test_historical_lead_arithmetic_is_explicitly_synthetic_only():
    from athena_procurement_arena.historical_case_report import historical_lead_status

    assert historical_lead_status(2_592_000.0) == "SUPPORTED"
    assert historical_lead_status(-2_592_000.0) == "NO_EARLY_ADVANTAGE"
    assert historical_lead_status(None) == "UNKNOWN"


def test_report_milestone_requires_declared_instant_in_explicit_release_quote():
    from athena_procurement_arena.historical_case_report import _valid_milestone
    from athena_procurement_arena.historical_cases import EvidenceSourceRef

    timestamp = "2021-02-01T00:00:00+00:00"
    ref = EvidenceSourceRef("e", "capture.json", "c", "h", "s", "https://example.gov",
        "Generation solicitation was released for this project.",
        {"release_event_at": timestamp,
         "milestone_semantic_evidence_quote": "Generation solicitation was released for this project."},
        "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", extra_fields={"archive_version_proof": {}})
    candidate = {"kind": "GENERATION_SOLICITATION_RELEASE", "verification": "VERIFIED", "at": timestamp,
                 "evidence_id": "e"}
    assert _valid_milestone({"e": ref}, candidate) is None
    quoted = EvidenceSourceRef("e", "capture.json", "c", "h", "s", "https://example.gov",
        f"Generation solicitation was released at {timestamp} for this project.",
        {"release_event_at": timestamp,
         "milestone_semantic_evidence_quote": f"Generation solicitation was released at {timestamp} for this project."},
        "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN",
        extra_fields={"archive_version_proof": {}, "observation_kind": "ARCHIVE_REPRESENTATION_OBSERVATION"})
    assert _valid_milestone({"e": quoted}, candidate) is None
    release = EvidenceSourceRef("e", "capture.json", "c", "h", "s", "https://example.gov",
        f"Generation solicitation was released at {timestamp} for this project.",
        {"release_event_at": timestamp,
         "milestone_semantic_evidence_quote": f"Generation solicitation was released at {timestamp} for this project."},
        "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN",
        extra_fields={"archive_version_proof": {}, "observation_kind": "VERIFIED_RELEASE_SOURCE"})
    assert _valid_milestone({"e": release}, candidate) == candidate


def test_report_actionability_rejects_empty_or_future_routes():
    from athena_procurement_arena.historical_case_report import _actionable_at
    from athena_procurement_arena.historical_cases import EvidenceSourceRef

    decision = [{"simulation_time": "2021-01-01T00:00:00+00:00", "action": "RESEARCH", "visible_evidence_ids": ["e"]}]
    common = {"buyer_organization": "Buyer", "project_responsibility_supported": True,
              "organization_evidence_quote": "Buyer", "usable_direct_route": True,
              "direct_route_evidence_quote": "", "direct_contact_email": ""}
    empty = EvidenceSourceRef("e", "capture.json", "c", "h", "s", "https://example.gov", "Buyer", common,
                              "UNKNOWN", "UNKNOWN", "2021-01-01T00:00:00+00:00", "UNKNOWN")
    assert _actionable_at(decision, {"e": empty}) is None
    future_claims = {**common, "direct_route_evidence_quote": "Buyer: buyer@example.gov",
                     "direct_contact_email": "buyer@example.gov"}
    future = EvidenceSourceRef("e", "capture.json", "c", "h", "s", "https://example.gov",
                               "Buyer: buyer@example.gov", future_claims, "UNKNOWN", "UNKNOWN",
                               "2021-01-02T00:00:00+00:00", "UNKNOWN")
    assert _actionable_at(decision, {"e": future}) is None


def test_archive_receipt_binds_original_url_memento_body_and_headers(tmp_path):
    from hashlib import sha256

    from athena_procurement_arena.historical_cases import EvidenceSourceRef, _verify_archive_version
    from athena_procurement_arena.public_capture import capture_markdown, write_capture

    root = tmp_path / "case"
    evidence = root / "evidence"
    evidence.mkdir(parents=True)
    original = "https://example.gov/project"
    archive = f"https://web.archive.org/web/20200102030405/{original}"
    observed = "2020-01-02T03:04:05+00:00"
    from athena_procurement_arena.historical_cases import archive_representation_text

    body = b"<p>Archived project statement</p>"
    headers = (b"HTTP/1.1 200 OK\nMemento-Datetime: Thu, 02 Jan 2020 03:04:05 GMT\n"
               b'Link: <https://example.gov/project>; rel="original"\n'
               b"Content-Type: text/plain\n")
    (evidence / "body.bin").write_bytes(body)
    (evidence / "headers.txt").write_bytes(headers)
    capture = capture_markdown(archive, archive_representation_text(body), capture_id="archive",
                               captured_by="test", captured_at=_iso("2026-01-01T00:00:00+00:00"))
    write_capture(capture, evidence / "capture.json")
    body_hash, header_hash = sha256(body).hexdigest(), sha256(headers).hexdigest()
    receipt = {"source_url": archive, "memento_datetime_utc": observed,
               "body_sha256": body_hash, "headers_sha256": header_hash}
    (evidence / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    proof = {"capture_path": "evidence/capture.json", "receipt_path": "evidence/receipt.json",
             "archive_url": archive, "original_url": original, "memento_datetime": observed,
             "body_path": "evidence/body.bin", "body_sha256": body_hash,
             "headers_path": "evidence/headers.txt", "headers_sha256": header_hash,
             "header_transformation": "Set-Cookie lines omitted; remaining header values unchanged"}
    ref = EvidenceSourceRef("e1", "evidence/capture.json", "archive", capture.capture_hash,
                            capture.content_sha256, archive, "Archived project statement", {},
                            "UNKNOWN", "UNKNOWN", observed, "UNKNOWN")
    _verify_archive_version(root, ref, _iso(observed), proof)
    (evidence / "body.bin").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="receipt mismatch"):
        _verify_archive_version(root, ref, _iso(observed), proof)


def test_historical_report_recomputes_replay_and_rejects_tampered_receipt(tmp_path):
    from athena_procurement_arena.historical_case_report import build_case_report
    from athena_procurement_arena.historical_cases import load_case, replay_case
    from athena_procurement_arena.policies import BaselineA

    root = Path(__file__).resolve().parents[2]
    case_path = root / "research/pre-rfp-history/cases/montauk-2021/case.json"
    case, scenario = load_case(case_path)
    replay = replay_case(case_path, mode="BACKTRACE", policy=BaselineA(), experiment_dir=tmp_path / "experiment")
    replay["ledger_verified"] = False
    replay["pre_rfp_ledger_verified"] = False
    report = build_case_report(case, scenario, replay, {})
    assert report["lead_status"] == "UNKNOWN"
    decisions_path = Path(replay["experiment_dir"]) / "decisions.json"
    payload = json.loads(decisions_path.read_text(encoding="utf-8"))
    payload["ledger_verified"] = False
    decisions_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        build_case_report(case, scenario, replay, {})


def test_known_alias_families_cannot_be_held_out_across_old_and_history_cases():
    root = Path(__file__).resolve().parents[2]
    montauk_old, _ = load_case(root / "research/pre-rfp-corpus/cases/PRF-002/case.json")
    montauk_new, _ = load_case(root / "research/pre-rfp-history/cases/montauk-2021/case.json")
    azure_old, _ = load_case(root / "research/pre-rfp-corpus/cases/PRF-007/case.json")
    azure_new, _ = load_case(root / "research/pre-rfp-history/cases/azure-sky-wind/case.json")
    assert montauk_old.procurement_family_id == montauk_new.procurement_family_id == "montauk-2021-2024"
    assert azure_old.procurement_family_id == azure_new.procurement_family_id == "azure-sky-commissioning"
    with pytest.raises(ValueError, match="procurement family split"):
        validate_family_splits([montauk_old, replace(montauk_new, holdout_group="HOLDOUT")])
    with pytest.raises(ValueError, match="procurement family split"):
        validate_family_splits([azure_old, replace(azure_new, holdout_group="HOLDOUT")])
