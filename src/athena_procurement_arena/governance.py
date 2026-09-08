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
class AthenaInput:
    frozen_state: dict[str, Any]
    decision: dict[str, Any]
    forecast: dict[str, Any]
    verified_outcome: dict[str, Any]
    evaluation: dict[str, Any]


@dataclass(frozen=True)
class Attribution:
    attribution_id: str
    input_ref: str
    correct_factors: tuple[str, ...] = ()
    failure_factors: tuple[str, ...] = ()
    confidence: float = 0.0

    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError("attribution confidence must be between 0 and 1")


@dataclass(frozen=True)
class CandidatePolicy:
    candidate_id: str
    source_lesson_id: str
    policy_version: str
    parameters: dict[str, Any]
    self_promoted: bool = False

    def __post_init__(self):
        if self.self_promoted:
            raise ValueError("Athena cannot self-promote a candidate policy")
        object.__setattr__(self, "parameters", dict(self.parameters))


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
