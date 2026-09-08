"""Explicit Athena learning artifacts and deterministic promotion gates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CandidateLesson:
    lesson_id: str
    hypothesis: str
    supporting_cohort: tuple[str, ...]
    counterexamples: tuple[str, ...]
    affected_policy: str
    proposed_change: dict[str, Any]
    expected_effect: dict[str, float]
    risks: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromotionDecision:
    candidate_id: str
    outcome: str
    reason: str
    metrics: dict[str, float | int]


class NegativeKnowledge:
    def __init__(self) -> None:
        self._lessons: dict[str, CandidateLesson] = {}

    def reject(self, lesson: CandidateLesson) -> None:
        self._lessons[lesson.lesson_id] = lesson

    def contains(self, lesson_id: str) -> bool:
        return lesson_id in self._lessons

    @property
    def lessons(self) -> tuple[CandidateLesson, ...]:
        return tuple(self._lessons.values())


def govern_candidate(candidate_id: str, incumbent_metrics: dict[str, float], candidate_metrics: dict[str, float],
                     *, invariant_failures: int, adversarial_pass: bool, counterfactual_pass: bool,
                     holdout_available: bool = False) -> PromotionDecision:
    """Return a decision; insufficient evidence never promotes."""
    if invariant_failures:
        return PromotionDecision(candidate_id, "REJECT", "hard invariant failure", candidate_metrics)
    if not adversarial_pass or not counterfactual_pass:
        return PromotionDecision(candidate_id, "QUARANTINE", "robustness gate failed", candidate_metrics)
    if not holdout_available:
        return PromotionDecision(candidate_id, "QUARANTINE", "sealed holdout evidence unavailable", candidate_metrics)
    improved = all(candidate_metrics.get(key, 0) >= value for key, value in incumbent_metrics.items())
    if not improved:
        return PromotionDecision(candidate_id, "REJECT", "no material objective improvement", candidate_metrics)
    return PromotionDecision(candidate_id, "PROMOTE", "all governed gates passed", candidate_metrics)
