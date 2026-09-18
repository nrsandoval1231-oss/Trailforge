from datetime import UTC, datetime

import pytest

from athena_procurement_arena.retrospective_evaluation import evaluate_retrospective
from athena_procurement_arena.retrospective_seal import (
    RetrospectiveOutcomeCohort,
    TraceOutcomeSeal,
    TraceOutcomeState,
)
from athena_procurement_arena.signal_ledger import SignalType
from athena_procurement_arena.trace_backtest import CohortTraceBacktest, TraceBacktest


def _seal(project_id: str, trace_hash: str, state: TraceOutcomeState) -> TraceOutcomeSeal:
    return TraceOutcomeSeal(f"seal-{project_id}", project_id, trace_hash, SignalType.PROCUREMENT_SIGNAL,
                            datetime(2026, 3, 1, tzinfo=UTC), state, "a" * 64, "quote", "statement",
                            "reviewer", datetime(2026, 3, 2, tzinfo=UTC),
                            source_url="https://example.com/outcome",
                            target_signal_id=f"target-{project_id}" if state == TraceOutcomeState.OBSERVED else None)


def _backtest() -> CohortTraceBacktest:
    cases = (
        {"project_id": "tp", "trace_hash": "1" * 64, "alerted": True, "matched": True,
         "earliest_signal_observed_at": "2026-01-01T00:00:00+00:00"},
        {"project_id": "fp", "trace_hash": "2" * 64, "alerted": True, "matched": False,
         "earliest_signal_observed_at": "2026-01-01T00:00:00+00:00"},
        {"project_id": "fn", "trace_hash": "3" * 64, "alerted": False, "matched": False},
        {"project_id": "tn", "trace_hash": "4" * 64, "alerted": False, "matched": False},
        {"project_id": "unknown", "trace_hash": "5" * 64, "alerted": True, "matched": False,
         "earliest_signal_observed_at": "2026-01-01T00:00:00+00:00"},
    )
    report = TraceBacktest(SignalType.PROCUREMENT_SIGNAL, (SignalType.FEASIBILITY_COMPLETE,),
                           5, 2, 1, 3, 1, (86400,), cases)
    return CohortTraceBacktest("cohort", "b" * 64, report)


def test_evaluation_reports_confusion_metrics_and_excludes_inconclusive() -> None:
    seals = (_seal("tp", "1" * 64, TraceOutcomeState.OBSERVED),
             _seal("fp", "2" * 64, TraceOutcomeState.NOT_OBSERVED_BY_CUTOFF),
             _seal("fn", "3" * 64, TraceOutcomeState.OBSERVED),
             _seal("tn", "4" * 64, TraceOutcomeState.NOT_OBSERVED_BY_CUTOFF),
             _seal("unknown", "5" * 64, TraceOutcomeState.INCONCLUSIVE))
    outcomes = RetrospectiveOutcomeCohort("outcomes", "b" * 64, SignalType.PROCUREMENT_SIGNAL,
                                          seals, "reviewer", datetime(2026, 3, 3, tzinfo=UTC))
    result = evaluate_retrospective(_backtest(), outcomes)
    assert (result.true_positive, result.false_positive, result.false_negative, result.true_negative) == (1, 1, 1, 1)
    assert result.precision == 0.5
    assert result.recall == 0.5
    assert result.false_alarm_rate == 0.5
    assert result.inconclusive_count == 1


def test_evaluation_rejects_mismatched_cohort_hash() -> None:
    outcomes = RetrospectiveOutcomeCohort(
        "outcomes", "c" * 64, SignalType.PROCUREMENT_SIGNAL,
        (_seal("tp", "1" * 64, TraceOutcomeState.OBSERVED),),
        "reviewer", datetime(2026, 3, 3, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="cohort hashes"):
        evaluate_retrospective(_backtest(), outcomes)


def test_evaluation_rejects_trace_replacement() -> None:
    outcomes = RetrospectiveOutcomeCohort(
        "outcomes", "b" * 64, SignalType.PROCUREMENT_SIGNAL,
        (_seal("tp", "f" * 64, TraceOutcomeState.OBSERVED),),
        "reviewer", datetime(2026, 3, 3, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="trace hash mismatch"):
        evaluate_retrospective(_backtest(), outcomes)


def test_alert_after_outcome_cutoff_is_not_counted_as_prediction() -> None:
    backtest = _backtest()
    cases = tuple(
        {**case, "earliest_signal_observed_at": "2026-04-01T00:00:00+00:00"}
        if case["project_id"] == "fp" else case
        for case in backtest.report.cases
    )
    repaired = CohortTraceBacktest(
        backtest.cohort_id, backtest.cohort_hash,
        TraceBacktest(SignalType.PROCUREMENT_SIGNAL, (SignalType.FEASIBILITY_COMPLETE,),
                      5, 2, 1, 3, 1, (86400,), cases),
    )
    outcomes = RetrospectiveOutcomeCohort(
        "outcomes", "b" * 64, SignalType.PROCUREMENT_SIGNAL,
        (_seal("fp", "2" * 64, TraceOutcomeState.NOT_OBSERVED_BY_CUTOFF),),
        "reviewer", datetime(2026, 3, 3, tzinfo=UTC),
    )
    result = evaluate_retrospective(repaired, outcomes)
    assert result.false_positive == 0
    assert result.true_negative == 1
