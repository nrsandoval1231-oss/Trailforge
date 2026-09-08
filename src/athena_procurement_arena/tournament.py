"""Deterministic tournament floors and Pareto comparison."""
from __future__ import annotations

from typing import Any

from .governance import govern_candidate


def meets_floors(metrics: dict[str, float], floors: dict[str, float]) -> bool:
    return all(metrics.get(name, float("-inf")) >= minimum for name, minimum in floors.items())

def pareto_dominates(candidate: dict[str, float], incumbent: dict[str, float], *, minimize=()) -> bool:
    keys = set(candidate) | set(incumbent)
    better_or_equal = True
    strictly_better = False
    for key in keys:
        left, right = candidate.get(key, float("-inf")), incumbent.get(key, float("-inf"))
        if key in minimize:
            left, right = -left, -right
        if left < right:
            better_or_equal = False
        if left > right:
            strictly_better = True
    return better_or_equal and strictly_better

def tournament_decision(candidate_id: str, candidate: dict[str, float], incumbent: dict[str, float],
                        *, invariant_failures: int = 0, floors=None) -> dict[str, Any]:
    floors = floors or {"recall": 0.0, "precision": 0.0}
    if invariant_failures:
        return {"candidate_id": candidate_id, "outcome": "REJECT", "reason": "hard invariant failure"}
    if not meets_floors(candidate, floors):
        return {"candidate_id": candidate_id, "outcome": "REJECT", "reason": "minimum floor failure"}
    if pareto_dominates(candidate, incumbent, minimize=("alerts", "cost")):
        return {"candidate_id": candidate_id, "outcome": "PROMOTE", "reason": "Pareto improvement"}
    return {"candidate_id": candidate_id, "outcome": "REJECT", "reason": "no Pareto improvement"}


def governed_tournament(candidate_id: str, candidate: dict[str, float], incumbent: dict[str, float], *,
                        invariant_failures: int = 0, adversarial_pass: bool = True,
                        counterfactual_pass: bool = True, holdout_available: bool = False) -> dict[str, Any]:
    decision = govern_candidate(candidate_id, incumbent, candidate,
                                invariant_failures=invariant_failures,
                                adversarial_pass=adversarial_pass,
                                counterfactual_pass=counterfactual_pass,
                                holdout_available=holdout_available)
    return {"candidate_id": decision.candidate_id, "outcome": decision.outcome,
            "reason": decision.reason, "metrics": decision.metrics}


def tournament_pipeline(candidate_id: str, candidate: dict[str, float], incumbent: dict[str, float], *,
                        invariant_failures: int = 0, floors=None, adversarial_pass: bool = True,
                        counterfactual_pass: bool = True, holdout_available: bool = False) -> dict[str, Any]:
    """Run the governed sequence and retain every gate result."""
    floors = floors or {"recall": 0.0, "precision": 0.0}
    gates = {"invariant": invariant_failures == 0,
             "minimum_floors": meets_floors(candidate, floors),
             "pareto": pareto_dominates(candidate, incumbent, minimize=("alerts", "cost")),
             "adversarial": adversarial_pass, "counterfactual": counterfactual_pass,
             "sealed_holdout": holdout_available}
    if not gates["invariant"] or not gates["minimum_floors"] or not gates["pareto"]:
        outcome = "REJECT"
    elif not gates["adversarial"] or not gates["counterfactual"] or not gates["sealed_holdout"]:
        outcome = "QUARANTINE"
    else:
        outcome = "PROMOTE"
    return {"candidate_id": candidate_id, "outcome": outcome, "gates": gates}
