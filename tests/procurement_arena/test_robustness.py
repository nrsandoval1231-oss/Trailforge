from datetime import datetime, timezone
from athena_procurement_arena import BaselineA, GroundTruth, Scenario
from athena_procurement_arena.robustness import counterfactual_sensitivity, paired_extension_worlds

def test_counterfactual_pair_is_minimally_different_and_replay_sensitive():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    base = Scenario("cf", "1", 7, (t,), (), GroundTruth("p", "CLOSED"))
    left, right = paired_extension_worlds(base)
    assert len(right.evidence) == len(left.evidence) + 1
    result = counterfactual_sensitivity(base, BaselineA.policy_id, BaselineA())
    assert result["changed"] is True
