from dataclasses import replace
from datetime import UTC, datetime, timedelta

from athena_procurement_arena import (
    BaselineA,
    EvidenceEvent,
    FrozenDecision,
    FrozenDecisionLedger,
    GroundTruth,
    Scenario,
    TemporalWorld,
)
from athena_procurement_arena.evaluation import (
    attention_metrics,
    evaluate_power_profile,
    evaluate_replay,
    useful_lead_time_seconds,
)


def test_evaluator_keeps_component_metrics_separate_and_unknown_power_explicit():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    event = EvidenceEvent("p1", "s", t, t, t, t, {"funded": True})
    scenario = Scenario("eval", "1", 3, (t,), (event,), GroundTruth("p1", "FUNDED"))
    world = TemporalWorld(scenario, BaselineA.policy_id, BaselineA())
    world.run()
    result = evaluate_replay(scenario, world.ledger.records)
    assert set(result.as_dict()) == {"discovery", "trail", "procurement", "power", "action", "efficiency", "invariant_status"}
    assert result.power["status"] == "UNAVAILABLE"
    assert result.discovery["precision"] == 1.0
    assert result.invariant_status == "PASS"

def test_evaluator_fails_on_corrupt_ledger_and_keeps_missing_basis_unknown():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    scenario = Scenario("eval", "1", 3, (t,), (), GroundTruth("p1", "FUNDED"))
    world = TemporalWorld(scenario, BaselineA.policy_id, BaselineA())
    world.run()
    assert evaluate_replay(scenario, ()).invariant_status == "UNKNOWN"
    corrupted = (replace(world.ledger.records[0], record_hash="bad"),)
    assert evaluate_replay(scenario, corrupted).invariant_status == "FAIL"

def test_evaluator_fails_verified_unauthorized_actions():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    scenario = Scenario("eval", "1", 3, (t,), (), GroundTruth("p1", "FUNDED"))
    for action in ("ENGAGE", "READY_FOR_AUTHORIZED_SUBMISSION"):
        ledger = FrozenDecisionLedger()
        ledger.append(FrozenDecision("eval", t, "policy", (), {}, action))
        assert ledger.verify()
        assert evaluate_replay(scenario, ledger.records).invariant_status == "FAIL"

def test_power_evaluator_reports_numeric_error_only_for_verified_truth():
    profile = ({"gap_mw": 6}, {"gap_mw": 0})
    assert evaluate_power_profile(profile, 6)["peak_gap_error_mw"] == 0
    assert evaluate_power_profile(profile, None)["status"] == "UNAVAILABLE"

def test_attention_metrics_penalize_alert_everything():
    metrics = attention_metrics(tuple(f"t{i}" for i in range(60)), frozenset({"t59"}))
    assert metrics["5"]["precision"] == 0 and metrics["50"]["recall"] == 0
    assert metrics["50"]["precision"] == 0

def test_useful_lead_time_requires_actionable_detection():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    assert useful_lead_time_seconds(t + timedelta(days=5), t, actionable=False) is None
    assert useful_lead_time_seconds(t + timedelta(days=5), t, actionable=True) == 432000
