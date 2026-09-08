import pytest

from athena_procurement_arena.athena_optimizer import (
    evaluate_policy,
    run_athena_optimization,
    weighted_threshold_policy,
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
    assert len(result["candidates"]) == 7
    assert result["search_space"] == {"weighted_thresholds": [2, 4, 6]}
    for item in result["candidates"].values():
        assert item["metrics"]["invariant_failures"] == 0
        assert item["gates"]["outcome"] in {"REJECT", "QUARANTINE"}
        assert item["candidate_policy"]["self_promoted"] is False


def test_weighted_threshold_is_bounded_and_tunable():
    with pytest.raises(ValueError):
        weighted_threshold_policy(-1)
    low = evaluate_policy("WEIGHTED_T2", weighted_threshold_policy(2), seed=7)
    high = evaluate_policy("WEIGHTED_T6", weighted_threshold_policy(6), seed=7)
    assert low["runs"] == high["runs"] == 40
    assert low["invariant_failures"] == high["invariant_failures"] == 0
    assert low["alerts"] >= high["alerts"]
