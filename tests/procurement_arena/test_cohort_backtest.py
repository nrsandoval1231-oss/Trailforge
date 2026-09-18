from datetime import UTC, datetime

from athena_procurement_arena.signal_ledger import EvidenceClass, ProjectSignal, ProjectTrace, SignalType, write_trace
from athena_procurement_arena.trace_backtest import backtest_cohort, write_cohort_backtest
from athena_procurement_arena.trace_cohort import build_trace_cohort, write_trace_cohort


def test_cohort_backtest_binds_report_to_cohort(tmp_path) -> None:
    trace_path = tmp_path / "trace.json"
    cohort_path = tmp_path / "cohort.json"
    report_path = tmp_path / "report.json"
    early = ProjectSignal("early", "project-a", datetime(2026, 1, 1, tzinfo=UTC),
                          SignalType.FEASIBILITY_COMPLETE, "Early", EvidenceClass.PUBLIC,
                          "0" * 64, "reviewer", {}, source_url="https://example.com/early")
    target = ProjectSignal("target", "project-a", datetime(2026, 2, 1, tzinfo=UTC),
                           SignalType.PROCUREMENT_SIGNAL, "Target", EvidenceClass.PUBLIC,
                           "1" * 64, "reviewer", {}, source_url="https://example.com/target")
    write_trace(ProjectTrace("project-a", (early, target)), trace_path)
    manifest = build_trace_cohort([str(trace_path)], cohort_id="cohort-a", assembled_by="reviewer",
                                  assembled_at=datetime(2026, 3, 1, tzinfo=UTC))
    write_trace_cohort(manifest, cohort_path)
    report = backtest_cohort(cohort_path, target_signal_type=SignalType.PROCUREMENT_SIGNAL,
                             early_signal_types=(SignalType.FEASIBILITY_COMPLETE,))
    write_cohort_backtest(report, report_path)
    assert report.cohort_hash == manifest.cohort_hash
    assert report.report.matched_cases == 1
    assert report.as_dict()["report_hash"]
