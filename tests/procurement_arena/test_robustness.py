from datetime import UTC, datetime

from athena_procurement_arena import BaselineA, GroundTruth, Scenario
from athena_procurement_arena.campaign import synthetic_scenario
from athena_procurement_arena.policies import buyer_frequency
from athena_procurement_arena.robustness import (
    adversarial_recurrence_world,
    counterfactual_sensitivity,
    counterfactual_suite,
    paired_extension_worlds,
)


def test_counterfactual_pair_is_minimally_different_and_replay_sensitive():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    base = Scenario("cf", "1", 7, (t,), (), GroundTruth("p", "CLOSED"))
    left, right = paired_extension_worlds(base)
    assert len(right.evidence) == len(left.evidence) + 1
    result = counterfactual_sensitivity(base, BaselineA.policy_id, BaselineA())
    assert result["changed"] is True

def test_amendment_adversary_does_not_create_three_procurements():
    world = adversarial_recurrence_world(4)
    assert buyer_frequency({"visible_evidence": world.evidence})[1] == "IGNORE"
    replay = __import__("athena_procurement_arena").TemporalWorld(world, BaselineA.policy_id, BaselineA())
    replay.run()
    assert replay.ledger.records[0].forecast["procurement"]["state"] == "UNKNOWN"

def test_required_counterfactual_suite_covers_five_decisive_facts():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    base = Scenario("suite", "1", 1, (t,), (), GroundTruth("p", "OPEN"))
    results = counterfactual_suite(base, BaselineA.policy_id, BaselineA())
    assert len(results) == 5
    assert {item["fact"]: item["expected_material_change"] for item in results} == {
        "contract_extension": True, "duplicate_procurement": False,
        "unknown_supply": False, "cancellation": True, "private_procurement": True,
    }
    assert all("passed" in item and "observed_material_change" in item for item in results)
    assert {item["fact"] for item in results if item["passed"]} == {
        "contract_extension", "duplicate_procurement", "unknown_supply", "private_procurement",
    }

    baseline = counterfactual_suite(synthetic_scenario(9), BaselineA.policy_id, BaselineA())
    assert {item["fact"] for item in baseline if item["passed"]} == {
        "contract_extension", "duplicate_procurement", "unknown_supply", "private_procurement",
    }
    assert [item["fact"] for item in baseline if not item["passed"]] == ["cancellation"]


def test_constant_policy_fails_required_change_despite_distinct_replay_hashes():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    base = Scenario("constant", "1", 9, (t,), (), GroundTruth("p", "OPEN"))

    def ignore(_state):
        return {"procurement": {"state": "UNKNOWN", "confidence": 0.0},
                "power": {"status": "UNKNOWN", "peak_gap_mw": None}}, "IGNORE"

    results = counterfactual_suite(base, "IGNORE", ignore)
    extension = next(item for item in results if item["fact"] == "contract_extension")
    assert extension["left_hash"] != extension["right_hash"]
    assert extension["changed"] is False
    assert extension["passed"] is False


def test_confidence_only_policy_fails_required_change_and_stability_inflation():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    base = Scenario("confidence-only", "1", 9, (t,), (), GroundTruth("p", "OPEN"))

    def confidence_only(state):
        claims = [item.claims for item in state["visible_evidence"]]
        confidence = 0.2 if any(any(name in row for name in (
            "contract_extension", "cancellation", "private_procurement",
            "duplicate_procurement", "unknown_supply",
        )) for row in claims) else 0.1
        return {"procurement": {"state": "UNKNOWN", "confidence": confidence},
                "power": {"status": "UNKNOWN", "peak_gap_mw": None}}, "IGNORE"

    results = counterfactual_suite(base, "CONFIDENCE_ONLY", confidence_only)
    by_fact = {item["fact"]: item for item in results}
    for fact in ("contract_extension", "cancellation", "private_procurement"):
        assert by_fact[fact]["observed_material_change"] is False
        assert by_fact[fact]["confidence_increased"] is True
        assert by_fact[fact]["passed"] is False
    for fact in ("duplicate_procurement", "unknown_supply"):
        assert by_fact[fact]["confidence_increased"] is True
        assert by_fact[fact]["passed"] is False
