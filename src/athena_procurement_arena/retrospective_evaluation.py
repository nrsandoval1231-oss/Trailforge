"""Deterministic evaluation of early-signal alerts against sealed outcomes."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from athena_arena.contracts import canonical_hash

from .retrospective_seal import RetrospectiveOutcomeCohort, TraceOutcomeState
from .signal_ledger import SignalType
from .trace_backtest import CohortTraceBacktest


@dataclass(frozen=True)
class RetrospectiveEvaluation:
    backtest_report_hash: str
    outcome_cohort_hash: str
    trace_cohort_hash: str
    target_signal_type: SignalType
    backtest_cases: int
    outcome_seals: int
    evaluated_count: int
    inconclusive_count: int
    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int
    missing_backtest_projects: tuple[str, ...]
    unsealed_backtest_projects: tuple[str, ...]

    @property
    def precision(self) -> float | None:
        denominator = self.true_positive + self.false_positive
        return round(self.true_positive / denominator, 6) if denominator else None

    @property
    def recall(self) -> float | None:
        denominator = self.true_positive + self.false_negative
        return round(self.true_positive / denominator, 6) if denominator else None

    @property
    def false_alarm_rate(self) -> float | None:
        denominator = self.false_positive + self.true_negative
        return round(self.false_positive / denominator, 6) if denominator else None

    @property
    def accuracy(self) -> float | None:
        return round((self.true_positive + self.true_negative) / self.evaluated_count, 6) \
            if self.evaluated_count else None

    @property
    def evaluation_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "trailforge-retrospective-evaluation-v1",
            "backtest_report_hash": self.backtest_report_hash,
            "outcome_cohort_hash": self.outcome_cohort_hash,
            "trace_cohort_hash": self.trace_cohort_hash,
            "target_signal_type": self.target_signal_type,
            "backtest_cases": self.backtest_cases,
            "outcome_seals": self.outcome_seals,
            "evaluated_count": self.evaluated_count,
            "inconclusive_count": self.inconclusive_count,
            "true_positive": self.true_positive,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
            "true_negative": self.true_negative,
            "precision": self.precision,
            "recall": self.recall,
            "false_alarm_rate": self.false_alarm_rate,
            "accuracy": self.accuracy,
            "missing_backtest_projects": list(self.missing_backtest_projects),
            "unsealed_backtest_projects": list(self.unsealed_backtest_projects),
            "evaluation_hash": self.evaluation_hash,
        }


def evaluate_retrospective(backtest: CohortTraceBacktest,
                           outcomes: RetrospectiveOutcomeCohort) -> RetrospectiveEvaluation:
    if backtest.cohort_hash != outcomes.trace_cohort_hash:
        raise ValueError("backtest and outcome cohort hashes do not match")
    if backtest.report.target_signal_type != outcomes.target_signal_type:
        raise ValueError("backtest and outcome target signal types do not match")
    cases = {str(case["project_id"]): case for case in backtest.report.cases}
    seals = {seal.project_id: seal for seal in outcomes.seals}
    true_positive = false_positive = false_negative = true_negative = 0
    inconclusive_count = 0
    missing: list[str] = []
    for seal in outcomes.seals:
        case = cases.get(seal.project_id)
        if case is None:
            missing.append(seal.project_id)
            continue
        if case.get("trace_hash") != seal.trace_hash:
            raise ValueError(f"trace hash mismatch for project: {seal.project_id}")
        if seal.outcome_state == TraceOutcomeState.INCONCLUSIVE:
            inconclusive_count += 1
            continue
        if "alerted" not in case:
            raise ValueError("backtest case does not expose alert status")
        predicted = bool(case["alerted"])
        if predicted:
            observed_at = case.get("earliest_signal_observed_at")
            if not observed_at:
                raise ValueError("alerted backtest case does not expose alert timestamp")
            predicted = datetime.fromisoformat(str(observed_at)) <= seal.cutoff_at
        observed = seal.outcome_state == TraceOutcomeState.OBSERVED
        if predicted and observed:
            true_positive += 1
        elif predicted:
            false_positive += 1
        elif observed:
            false_negative += 1
        else:
            true_negative += 1
    evaluated_count = true_positive + false_positive + false_negative + true_negative
    unsealed = sorted(set(cases) - set(seals))
    return RetrospectiveEvaluation(
        backtest.report_hash, outcomes.cohort_hash, backtest.cohort_hash,
        outcomes.target_signal_type, len(cases), len(outcomes.seals), evaluated_count,
        inconclusive_count, true_positive, false_positive, false_negative, true_negative,
        tuple(sorted(missing)), tuple(unsealed),
    )


def write_retrospective_evaluation(evaluation: RetrospectiveEvaluation, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"retrospective evaluation output already exists: {destination}")
    destination.write_text(json.dumps(evaluation.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
