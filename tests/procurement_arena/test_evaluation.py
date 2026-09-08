from datetime import datetime, timezone
from athena_procurement_arena import BaselineA, EvidenceEvent, GroundTruth, Scenario, TemporalWorld
from athena_procurement_arena.evaluation import evaluate_replay
from athena_procurement_arena.evaluation import evaluate_power_profile

def test_evaluator_keeps_component_metrics_separate_and_unknown_power_explicit():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    event = EvidenceEvent("p1", "s", t, t, t, t, {"funded": True})
    scenario = Scenario("eval", "1", 3, (t,), (event,), GroundTruth("p1", "FUNDED"))
    world = TemporalWorld(scenario, BaselineA.policy_id, BaselineA())
    world.run()
    result = evaluate_replay(scenario, world.ledger.records)
    assert set(result.as_dict()) == {"discovery", "trail", "procurement", "power", "action", "efficiency", "invariant_status"}
    assert result.power["status"] == "UNAVAILABLE"
    assert result.discovery["precision"] == 1.0

def test_power_evaluator_reports_numeric_error_only_for_verified_truth():
    profile = ({"gap_mw": 6}, {"gap_mw": 0})
    assert evaluate_power_profile(profile, 6)["peak_gap_error_mw"] == 0
    assert evaluate_power_profile(profile, None)["status"] == "UNAVAILABLE"
