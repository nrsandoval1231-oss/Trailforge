from datetime import UTC, datetime, timedelta

import pytest

from athena_procurement_arena import EvidenceClass, ProjectSignal, ProjectTrace, SignalType
from athena_procurement_arena.trace_backtest import backtest_traces


def _signal(signal_id, signal_type, days):
    return ProjectSignal(
        signal_id=signal_id, project_id="project-1",
        observed_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=days),
        signal_type=signal_type, title=signal_type.value, evidence_class=EvidenceClass.PUBLIC,
        source_url="https://example.com/" + signal_id, source_sha256="a" * 64,
        verified_by="reviewer", claims={}, source_quote=signal_type.value,
    )


def test_backtest_measures_earliest_signal_to_observed_target():
    trace = ProjectTrace("project-1", (
        _signal("power", SignalType.POWER_REQUIREMENT, 10),
        _signal("feasibility", SignalType.FEASIBILITY_COMPLETE, 1),
        _signal("procurement", SignalType.PROCUREMENT_SIGNAL, 40),
    ))
    report = backtest_traces((trace,), target_signal_type=SignalType.PROCUREMENT_SIGNAL,
                             early_signal_types=(SignalType.FEASIBILITY_COMPLETE, SignalType.POWER_REQUIREMENT))
    assert report.coverage == 1.0
    assert report.matched_cases == 1
    assert report.lead_seconds == (39 * 86400,)
    assert report.cases[0]["earliest_signal_id"] == "feasibility"


def test_backtest_keeps_missing_target_and_missing_early_signal_unresolved():
    target_without_early = ProjectTrace("project-1", (_signal("target", SignalType.PROCUREMENT_SIGNAL, 2),))
    no_target = ProjectTrace("project-2", (
        ProjectSignal("announce", "project-2", datetime(2026, 1, 1, tzinfo=UTC), SignalType.PROJECT_ANNOUNCED,
                      "Announcement", EvidenceClass.PUBLIC, "b" * 64, "reviewer", {},
                      source_url="https://example.com/announce"),
    ))
    report = backtest_traces((target_without_early, no_target), target_signal_type=SignalType.PROCUREMENT_SIGNAL,
                             early_signal_types=(SignalType.FEASIBILITY_COMPLETE,))
    assert report.target_cases == 1
    assert report.unresolved_without_target == 1
    assert report.unresolved_without_early_signal == 1
    assert report.coverage == 0.0
    assert len(report.cases) == 2
    assert {case["project_id"] for case in report.cases} == {"project-1", "project-2"}
    assert all(case["trace_hash"] for case in report.cases)


def test_backtest_requires_early_signal_types():
    with pytest.raises(ValueError, match="early signal"):
        backtest_traces((), target_signal_type=SignalType.OPERATING, early_signal_types=())
