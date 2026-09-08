from datetime import datetime, timezone, timedelta

import pytest

from athena_procurement_arena import (
    EvidenceEvent, FrozenDecision, FrozenDecisionLedger, GroundTruth, InvariantViolation,
    IdentityResolution, PowerNeed, PowerScope, Scenario, Supply, calculate_power_gap, calculate_power_profile, deduplicate_evidence, resolve_identity, validate_power_scopes, validate_recommended_action, validate_scenario,
)

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def evidence(eid, available, *, prediction=False):
    return EvidenceEvent(eid, "source", T0, T0, available, available, {"x": 1}, is_prediction=prediction)


def scenario(items=(evidence("e1", T0),)):
    return Scenario("s1", "1", 7, (T0, T0 + timedelta(days=1)), tuple(items), GroundTruth("p1", "OPEN"))


def test_temporal_cutoff_and_exact_replay_hash():
    s = scenario((evidence("old", T0), evidence("future", T0 + timedelta(days=2))))
    assert [e.evidence_id for e in s.evidence if e.visible_at(T0)] == ["old"]
    assert validate_scenario(s) == validate_scenario(s)


def test_prediction_as_evidence_is_invalid():
    with pytest.raises(InvariantViolation, match="prediction"):
        validate_scenario(scenario((evidence("p", T0), evidence("pred", T0, prediction=True))))


def test_unknown_supply_is_not_zero_and_partial_supply_is_gap():
    need = PowerNeed("n", PowerScope.CONSTRUCTION, T0, T0 + timedelta(hours=1), 10, None)
    assert calculate_power_gap(need)["status"] == "UNKNOWN"
    known = PowerNeed("n", PowerScope.CONSTRUCTION, T0, T0 + timedelta(hours=1), 10, 4)
    assert calculate_power_gap(known)["peak_gap_mw"] == 6
    assert calculate_power_gap(known, (Supply(T0, T0 + timedelta(hours=1), None),))["status"] == "UNKNOWN"


def test_ledger_is_hash_chained_and_rejects_rewrite():
    ledger = FrozenDecisionLedger()
    first = ledger.append(FrozenDecision("s1", T0, "BASELINE_A", ("e1",), {"p": 1}, "WATCH"))
    second = ledger.append(FrozenDecision("s1", T0 + timedelta(days=1), "BASELINE_A", ("e1",), {"p": 2}, "RESEARCH"))
    assert first.record_hash and second.previous_hash == first.record_hash and ledger.verify()
    with pytest.raises(InvariantViolation):
        ledger.append(first)

def test_evidence_and_decision_snapshots_are_detached():
    claims = {"stage": "funded"}
    item = evidence("immutable", T0)
    assert item.claims["x"] == 1
    with pytest.raises(TypeError):
        item.claims["x"] = 2
    decision = FrozenDecision("s", T0, "p", (), {"nested": "value"}, "WATCH")
    with pytest.raises(TypeError):
        decision.forecast["nested"] = "changed"

def test_tenant_and_commercial_action_invariants_are_fail_closed():
    foreign = EvidenceEvent("foreign", "s", T0, T0, T0, T0, tenant_id="other")
    with pytest.raises(InvariantViolation, match="I-07"):
        validate_scenario(scenario((foreign,)))
    with pytest.raises(InvariantViolation, match="I-10"):
        validate_recommended_action("ENGAGE")
    validate_recommended_action("ENGAGE", human_approved=True)

def test_lineage_deduplication_and_conservative_identity_resolution():
    one = EvidenceEvent("one", "source-a", T0, T0, T0, T0, lineage_family="wire-1")
    two = EvidenceEvent("two", "source-b", T0, T0, T0, T0, lineage_family="wire-1")
    assert tuple(item.evidence_id for item in deduplicate_evidence((one, two))) == ("one",)
    assert resolve_identity(authoritative_ids=("project-1", "project-1")) == IdentityResolution.MERGE
    assert resolve_identity(name="same name", geography="same city") == IdentityResolution.PROVISIONAL

def test_overlapping_same_scope_is_rejected():
    a = PowerNeed("a", PowerScope.CONSTRUCTION, T0, T0 + timedelta(hours=2), 1, 1)
    b = PowerNeed("b", PowerScope.CONSTRUCTION, T0 + timedelta(hours=1), T0 + timedelta(hours=3), 1, 1)
    with pytest.raises(InvariantViolation, match="I-12"):
        validate_power_scopes((a, b))

def test_power_profile_handles_phased_supply_and_unknown_segments():
    need = PowerNeed("n", PowerScope.COMMISSIONING, T0, T0 + timedelta(hours=3), 10, 0)
    known = Supply(T0, T0 + timedelta(hours=1), 4)
    unknown = Supply(T0 + timedelta(hours=1), T0 + timedelta(hours=2), None)
    full = Supply(T0 + timedelta(hours=2), T0 + timedelta(hours=3), 10)
    profile = calculate_power_profile((need,), (known, unknown, full))
    assert profile[0]["gap_mw"] == 6 and profile[0]["status"] == "GAP"
    assert profile[1]["status"] == "UNKNOWN" and profile[2]["status"] == "NO_GAP"
