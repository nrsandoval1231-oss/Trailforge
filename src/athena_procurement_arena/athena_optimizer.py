"""Deterministic Athena adapter for bounded policy optimization."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .campaign import synthetic_scenario
from .evaluation import evaluate_replay
from .governance import AthenaInput, CandidateLesson, CandidatePolicy
from .policies import (
    BaselineA,
    buyer_frequency,
    keyword_rfp,
    latest_event,
    static_weighted_score,
)
from .robustness import adversarial_recurrence_world, counterfactual_suite
from .scenarios import SCENARIO_FAMILIES, family_scenario
from .tournament import tournament_pipeline
from .world import TemporalWorld

Policy = Callable[[Mapping[str, Any]], tuple[dict[str, Any], str]]


def weighted_threshold_policy(threshold: int) -> Policy:
    """Build a policy whose only tunable parameter is the action threshold."""
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    weights = {"capital": 2, "funded": 2, "permit": 1, "engineering": 1, "rfp": 4, "budget": 2}

    def policy(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
        text = " ".join(
            str(item.get("claims", {}) if isinstance(item, Mapping) else getattr(item, "claims", {})).lower()
            for item in state.get("visible_evidence", ())
        )
        score = sum(weight for word, weight in weights.items() if word in text)
        action = "PREPARE" if score >= threshold and score else ("RESEARCH" if score else "IGNORE")
        return {"score": score, "threshold": threshold}, action

    return policy


def evaluate_policy(policy_id: str, policy: Policy, *, seed: int = 1) -> dict[str, Any]:
    """Evaluate a policy on every registered family without using future evidence."""
    rows = []
    invariant_failures = 0
    for index, family in enumerate(SCENARIO_FAMILIES):
        scenario = family_scenario(family, seed + index)
        world = TemporalWorld(scenario, policy_id, policy)
        world.run()
        invariant_failures += int(not world.ledger.verify())
        rows.append(evaluate_replay(scenario, world.ledger.records))
    recalls = [float(row.discovery["recall"]) for row in rows]
    precisions = [float(row.discovery["precision"] or 0.0) for row in rows]
    actionable = sum(int(row.action["actionable_steps"] or 0) for row in rows)
    attention = sum(int(row.action["attention_burden"] or 0) for row in rows)
    count = len(rows)
    return {
        "runs": count,
        "invariant_failures": invariant_failures,
        "recall": round(sum(recalls) / count, 6),
        "precision": round(sum(precisions) / count, 6),
        "alerts": actionable,
        "cost": attention,
        "actionable_steps": actionable,
    }


def _robustness_pass(policy_id: str, policy: Policy, seed: int) -> tuple[bool, bool]:
    adversarial = TemporalWorld(adversarial_recurrence_world(seed), policy_id, policy)
    adversarial.run()
    adversarial_pass = adversarial.ledger.verify() and all(
        record.forecast.get("procurement", {}).get("state", "UNKNOWN") == "UNKNOWN"
        and record.action not in {"RESEARCH", "PREPARE", "BID_REVIEW"}
        for record in adversarial.ledger.records
    )
    cases = counterfactual_suite(synthetic_scenario(seed), policy_id, policy)
    counterfactual_pass = all(case["changed"] for case in cases)
    return adversarial_pass, counterfactual_pass


def run_athena_optimization(*, seed: int = 1, holdout_available: bool = False) -> dict[str, Any]:
    """Run Athena's candidate loop; promotion remains human/holdout gated."""
    incumbent_id = "BASELINE_A"
    incumbent: Policy = BaselineA()
    candidates: dict[str, Policy] = {
        "KEYWORD": keyword_rfp,
        "STATIC_WEIGHTED": static_weighted_score,
        "LATEST_EVENT": latest_event,
        "BUYER_FREQUENCY": buyer_frequency,
        **{f"WEIGHTED_T{threshold}": weighted_threshold_policy(threshold) for threshold in (2, 4, 6)},
    }
    incumbent_metrics = evaluate_policy(incumbent_id, incumbent, seed=seed)
    results: dict[str, Any] = {}
    for candidate_id, policy in candidates.items():
        metrics = evaluate_policy(candidate_id, policy, seed=seed)
        adversarial_pass, counterfactual_pass = _robustness_pass(candidate_id, policy, seed)
        lesson = CandidateLesson(
            lesson_id=f"lesson-{candidate_id.lower()}",
            hypothesis=f"Evaluate whether {candidate_id} improves evidence efficiency over {incumbent_id}.",
            supporting_cohort=SCENARIO_FAMILIES,
            counterexamples=tuple(family for family in SCENARIO_FAMILIES if metrics["recall"] < incumbent_metrics["recall"]),
            affected_policy=incumbent_id,
            proposed_change={"candidate_policy": candidate_id},
            expected_effect={"recall": metrics["recall"], "precision": metrics["precision"]},
        )
        candidate = CandidatePolicy(candidate_id, lesson.lesson_id, "1", {"policy_id": candidate_id})
        gates = tournament_pipeline(
            candidate_id,
            metrics,
            incumbent_metrics,
            invariant_failures=metrics["invariant_failures"],
            floors={"recall": 0.0, "precision": 0.0},
            adversarial_pass=adversarial_pass,
            counterfactual_pass=counterfactual_pass,
            holdout_available=holdout_available,
        )
        results[candidate_id] = {
            "metrics": metrics,
            "athena_input": AthenaInput(
                frozen_state={"seed": seed, "families": len(SCENARIO_FAMILIES)},
                decision={"policy_id": candidate_id},
                forecast={"candidate": candidate_id},
                verified_outcome={"holdout_available": holdout_available},
                evaluation=metrics,
            ).__dict__,
            "lesson": lesson.__dict__,
            "candidate_policy": candidate.__dict__,
            "gates": gates,
        }
    return {
        "status": "PASS",
        "seed": seed,
        "incumbent": {"policy_id": incumbent_id, "metrics": incumbent_metrics},
        "holdout_available": holdout_available,
        "search_space": {"weighted_thresholds": [2, 4, 6]},
        "candidates": results,
        "promotion_count": sum(item["gates"]["outcome"] == "PROMOTE" for item in results.values()),
    }
