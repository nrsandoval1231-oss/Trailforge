from datetime import datetime, timezone
from athena_procurement_arena import BaselineA, GroundTruth, Scenario
from athena_procurement_arena.robustness import adversarial_recurrence_world, counterfactual_sensitivity, paired_extension_worlds
from athena_procurement_arena.policies import buyer_frequency

def test_counterfactual_pair_is_minimally_different_and_replay_sensitive():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    base = Scenario("cf", "1", 7, (t,), (), GroundTruth("p", "CLOSED"))
    left, right = paired_extension_worlds(base)
    assert len(right.evidence) == len(left.evidence) + 1
    result = counterfactual_sensitivity(base, BaselineA.policy_id, BaselineA())
    assert result["changed"] is True

def test_amendment_adversary_does_not_create_three_procurements():
    world = adversarial_recurrence_world(4)
    assert buyer_frequency({"visible_evidence": world.evidence})[1] == "RESEARCH"
    replay = __import__("athena_procurement_arena").TemporalWorld(world, BaselineA.policy_id, BaselineA())
    replay.run()
    assert replay.ledger.records[0].forecast["procurement"]["state"] == "UNKNOWN"
