"""Explicit Athena learning artifacts and deterministic promotion gates."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
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
    SNAPSHOT_SCHEMA = "athena-negative-knowledge"
    SNAPSHOT_VERSION = 1
    # Idea identity excludes evaluated effects/counterexamples, which are outcomes
    # of running the candidate. The remaining fields describe the proposed idea.

    def __init__(self) -> None:
        self._lessons: dict[str, CandidateLesson] = {}

    @staticmethod
    def _lesson_data(lesson: CandidateLesson) -> dict[str, Any]:
        return {
            "lesson_id": lesson.lesson_id, "hypothesis": lesson.hypothesis,
            "supporting_cohort": list(lesson.supporting_cohort),
            "counterexamples": list(lesson.counterexamples),
            "affected_policy": lesson.affected_policy,
            "proposed_change": deepcopy(lesson.proposed_change),
            "expected_effect": deepcopy(lesson.expected_effect), "risks": list(lesson.risks),
        }

    @staticmethod
    def _lesson_from_data(data: dict[str, Any]) -> CandidateLesson:
        expected = {"lesson_id", "hypothesis", "supporting_cohort", "counterexamples",
                    "affected_policy", "proposed_change", "expected_effect", "risks"}
        if not isinstance(data, dict) or set(data) != expected:
            raise ValueError("malformed negative knowledge lesson")
        if not all(isinstance(data[k], str) for k in ("lesson_id", "hypothesis", "affected_policy")):
            raise ValueError("malformed negative knowledge lesson fields")
        if not all(isinstance(data[k], list) and all(isinstance(v, str) for v in data[k])
                   for k in ("supporting_cohort", "counterexamples", "risks")):
            raise ValueError("malformed negative knowledge cohorts")
        if not isinstance(data["proposed_change"], dict) or not isinstance(data["expected_effect"], dict):
            raise ValueError("malformed negative knowledge effects")
        return CandidateLesson(data["lesson_id"], data["hypothesis"], tuple(data["supporting_cohort"]),
                               tuple(data["counterexamples"]), data["affected_policy"],
                               data["proposed_change"], data["expected_effect"], tuple(data["risks"]))

    @staticmethod
    def _canonical_digest(value: Any) -> str:
        serialized = json.dumps(value, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=False, allow_nan=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def _exact_digest(cls, lesson: CandidateLesson) -> str:
        return cls._canonical_digest(cls._lesson_data(lesson))

    @classmethod
    def _idea_digest(cls, lesson_id: str, hypothesis: str, supporting_cohort: tuple[str, ...],
                     affected_policy: str, proposed_change: dict[str, Any],
                     risks: tuple[str, ...] = ()) -> str:
        return cls._canonical_digest({
            "lesson_id": lesson_id, "hypothesis": hypothesis,
            "supporting_cohort": list(supporting_cohort), "affected_policy": affected_policy,
            "proposed_change": proposed_change, "risks": list(risks),
        })

    def reject(self, lesson: CandidateLesson) -> str:
        existing = self._lessons.get(lesson.lesson_id)
        if existing is not None:
            return "REJECTED" if self._exact_digest(existing) == self._exact_digest(lesson) else "CONFLICT"
        detached = self._lesson_from_data(json.loads(json.dumps(self._lesson_data(lesson), allow_nan=False)))
        self._lessons[lesson.lesson_id] = detached
        return "REJECTED"

    def contains(self, lesson_id: str) -> bool:
        return lesson_id in self._lessons

    def match(self, lesson: CandidateLesson) -> bool:
        existing = self._lessons.get(lesson.lesson_id)
        return existing is not None and self._exact_digest(existing) == self._exact_digest(lesson)

    def conflict(self, lesson: CandidateLesson) -> bool:
        return lesson.lesson_id in self._lessons and not self.match(lesson)

    def classify_idea(self, lesson_id: str, hypothesis: str, supporting_cohort: tuple[str, ...],
                      affected_policy: str, proposed_change: dict[str, Any],
                      risks: tuple[str, ...] = ()) -> str:
        """Classify stable proposed-idea content before candidate execution."""
        existing = self._lessons.get(lesson_id)
        if existing is None:
            return "NEW"
        proposed_digest = self._idea_digest(lesson_id, hypothesis, supporting_cohort,
                                            affected_policy, proposed_change, risks)
        existing_digest = self._idea_digest(
            existing.lesson_id, existing.hypothesis, existing.supporting_cohort,
            existing.affected_policy, existing.proposed_change, existing.risks,
        )
        return "REJECTED" if proposed_digest == existing_digest else "CONFLICT"

    def lesson_digest(self, lesson_id: str) -> str | None:
        """Return the exact persisted lesson digest for audit output."""
        lesson = self._lessons.get(lesson_id)
        return None if lesson is None else self._exact_digest(lesson)

    def save(self, path: str | Path) -> None:
        target = Path(path)
        lessons = [self._lesson_data(item) for item in sorted(self._lessons.values(), key=lambda x: x.lesson_id)]
        payload = {"schema": self.SNAPSHOT_SCHEMA, "version": self.SNAPSHOT_VERSION, "lessons": lessons}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        snapshot = {**payload, "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(snapshot, stream, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")

    @classmethod
    def load(cls, path: str | Path) -> NegativeKnowledge:
        try:
            snapshot = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("invalid negative knowledge snapshot") from exc
        if not isinstance(snapshot, dict) or set(snapshot) != {"schema", "version", "lessons", "sha256"}:
            raise ValueError("mismatched negative knowledge snapshot schema")
        payload = {key: snapshot[key] for key in ("schema", "version", "lessons")}
        if payload["schema"] != cls.SNAPSHOT_SCHEMA or payload["version"] != cls.SNAPSHOT_VERSION or not isinstance(payload["lessons"], list):
            raise ValueError("mismatched negative knowledge snapshot schema")
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        if not isinstance(snapshot["sha256"], str) or hashlib.sha256(canonical.encode("utf-8")).hexdigest() != snapshot["sha256"]:
            raise ValueError("negative knowledge snapshot hash mismatch")
        store = cls()
        for data in payload["lessons"]:
            lesson = cls._lesson_from_data(data)
            if lesson.lesson_id in store._lessons:
                raise ValueError("duplicate negative knowledge lesson id")
            store._lessons[lesson.lesson_id] = lesson
        return store

    @property
    def lessons(self) -> tuple[CandidateLesson, ...]:
        return tuple(self._lesson_from_data(self._lesson_data(item)) for item in self._lessons.values())


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
