from datetime import UTC, datetime

import pytest

from athena_procurement_arena.retrospective_seal import (
    RetrospectiveOutcomeCohort,
    TraceOutcomeState,
    build_outcome_cohort,
    seal_trace_outcome,
    write_outcome_seal,
)
from athena_procurement_arena.signal_ledger import EvidenceClass, ProjectSignal, ProjectTrace, SignalType


def _trace() -> ProjectTrace:
    early = ProjectSignal("early", "project-a", datetime(2026, 1, 1, tzinfo=UTC), SignalType.FEASIBILITY_COMPLETE,
                          "Early", EvidenceClass.PUBLIC, "0" * 64, "reviewer", {}, source_url="https://example.com/early")
    target = ProjectSignal("target", "project-a", datetime(2026, 2, 1, tzinfo=UTC), SignalType.PROCUREMENT_SIGNAL,
                           "Target", EvidenceClass.PUBLIC, "1" * 64, "reviewer", {}, source_url="https://example.com/target")
    return ProjectTrace("project-a", (early, target))


def _seal(trace: ProjectTrace, state: TraceOutcomeState):
    return seal_trace_outcome(trace, seal_id=f"seal-{state}", target_signal_type=SignalType.PROCUREMENT_SIGNAL,
                              cutoff_at=datetime(2026, 3, 1, tzinfo=UTC), outcome_state=state,
                              source_sha256="2" * 64, source_quote="Reviewer evidence", reviewer_statement="Reviewed.",
                              reviewed_by="reviewer", reviewed_at=datetime(2026, 3, 2, tzinfo=UTC),
                              evidence_class=EvidenceClass.PUBLIC, source_url="https://example.com/review",
                              target_signal_id="target" if state == TraceOutcomeState.OBSERVED else None)


def test_observed_seal_binds_trace_and_target() -> None:
    seal = _seal(_trace(), TraceOutcomeState.OBSERVED)
    assert seal.trace_hash == _trace().trace_hash
    assert seal.target_signal_id == "target"


def test_not_observed_requires_no_target_and_rejects_existing_target() -> None:
    with pytest.raises(ValueError, match="contains an observed target"):
        _seal(_trace(), TraceOutcomeState.NOT_OBSERVED_BY_CUTOFF)


def test_outcome_cohort_counts_explicit_states(tmp_path) -> None:
    trace = _trace()
    seal = _seal(trace, TraceOutcomeState.OBSERVED)
    seal_path = tmp_path / "seal.json"
    write_outcome_seal(seal, seal_path)
    cohort = build_outcome_cohort([str(seal_path)], cohort_id="outcomes-1", trace_cohort_hash="3" * 64,
                                  target_signal_type=SignalType.PROCUREMENT_SIGNAL, created_by="reviewer",
                                  created_at=datetime(2026, 3, 3, tzinfo=UTC))
    assert isinstance(cohort, RetrospectiveOutcomeCohort)
    assert cohort.observed_count == 1
    assert cohort.not_observed_count == 0
