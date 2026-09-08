"""Deterministic tournament floors and Pareto comparison."""
from __future__ import annotations
from typing import Any

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
