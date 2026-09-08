from athena_procurement_arena.athena_optimizer import (
    evaluate_policy,
    run_athena_optimization,
)
from athena_procurement_arena.policies import BaselineA


def test_athena_evaluation_is_family_complete_and_deterministic():
    left = evaluate_policy("BASELINE_A", BaselineA(), seed=7)
    right = evaluate_policy("BASELINE_A", BaselineA(), seed=7)
    assert left == right
    assert left["runs"] == 40
    assert left["invariant_failures"] == 0


def test_athena_loop_quarantines_without_holdout_and_emits_artifacts():
    result = run_athena_optimization(seed=7)
    assert result["status"] == "PASS"
    assert result["promotion_count"] == 0
    assert set(result["candidates"]) == {"KEYWORD", "STATIC_WEIGHTED", "LATEST_EVENT", "BUYER_FREQUENCY"}
    for item in result["candidates"].values():
        assert item["metrics"]["invariant_failures"] == 0
        assert item["gates"]["outcome"] in {"REJECT", "QUARANTINE"}
        assert item["candidate_policy"]["self_promoted"] is False
