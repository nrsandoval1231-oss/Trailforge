from datetime import UTC, datetime, timedelta

from athena_procurement_arena import EvidenceClass, ProjectSignal, ProjectTrace, SignalType
from athena_procurement_arena.signal_family_report import compare_signal_families


def _sig(project, sid, kind, day, **claims):
    return ProjectSignal(
        signal_id=f"{project}-{sid}", project_id=project,
        observed_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=day), signal_type=kind,
        title=sid, evidence_class=EvidenceClass.PUBLIC, source_url="https://example.com/" + sid,
        source_sha256="a" * 64, verified_by="reviewer", claims=claims, source_quote=sid)


def test_families_compared_independently_with_burden_unresolved_surfaces_and_buyer_path():
    p1 = ProjectTrace("p1", (
        _sig("p1", "a", SignalType.PERMIT_FILED, 0, buyer_path=["EPCM"]),
        _sig("p1", "b", SignalType.PERMIT_FILED, 5),
        _sig("p1", "c", SignalType.EPCM_AWARDED, 30),
        _sig("p1", "t", SignalType.PROCUREMENT_SIGNAL, 100),
    ))
    p2 = ProjectTrace("p2", (_sig("p2", "a", SignalType.PERMIT_FILED, 0),))
    p3 = ProjectTrace("p3", (_sig("p3", "t", SignalType.PROCUREMENT_SIGNAL, 10),))
    report = compare_signal_families((p1, p2, p3), target_signal_type=SignalType.PROCUREMENT_SIGNAL)
    by_type = {item.signal_type: item for item in report.families}
    permit = by_type[SignalType.PERMIT_FILED]
    assert (permit.target_cases, permit.surfaced_cases, permit.matched_cases) == (2, 2, 1)
    assert permit.unresolved_surfaces == 1 and permit.coverage == 0.5
    assert permit.median_lead_days == 100 and permit.signals_per_surfaced_project == 1.5
    assert permit.buyer_path_cases == 1 and not permit.repeatable
    assert by_type[SignalType.EPCM_AWARDED].median_lead_days == 70
    assert report.projects_with_target == 2
    assert report.cohort_status.startswith("BELOW_TARGET")
    assert report.report_hash == compare_signal_families(
        (p3, p2, p1), target_signal_type=SignalType.PROCUREMENT_SIGNAL).report_hash
