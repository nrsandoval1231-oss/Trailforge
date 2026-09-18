from datetime import UTC, datetime

import pytest

from athena_procurement_arena.signal_ledger import EvidenceClass, ProjectSignal, ProjectTrace, SignalType, write_trace
from athena_procurement_arena.trace_cohort import build_trace_cohort, load_trace_cohort, write_trace_cohort


def _trace(project_id: str, signal_id: str) -> ProjectTrace:
    signal = ProjectSignal(signal_id, project_id, datetime(2026, 1, 1, tzinfo=UTC),
                            SignalType.PROJECT_ANNOUNCED, project_id, EvidenceClass.PUBLIC,
                            "0" * 64, "reviewer", {}, source_url="https://example.com/source")
    return ProjectTrace(project_id, (signal,))


def test_cohort_round_trip_verifies_members(tmp_path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    output = tmp_path / "cohort.json"
    write_trace(_trace("project-a", "signal-a"), first)
    write_trace(_trace("project-b", "signal-b"), second)
    manifest = build_trace_cohort([str(first), str(second)], cohort_id="cohort-1",
                                  assembled_by="reviewer", assembled_at=datetime(2026, 2, 1, tzinfo=UTC))
    write_trace_cohort(manifest, output)
    loaded, traces = load_trace_cohort(output)
    assert loaded.cohort_hash == manifest.cohort_hash
    assert [trace.project_id for trace in traces] == ["project-a", "project-b"]


def test_duplicate_project_ids_fail_closed(tmp_path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    write_trace(_trace("project-a", "signal-a"), first)
    write_trace(_trace("project-a", "signal-b"), second)
    with pytest.raises(ValueError, match="duplicate project IDs"):
        build_trace_cohort([str(first), str(second)], cohort_id="cohort-1",
                           assembled_by="reviewer", assembled_at=datetime(2026, 2, 1, tzinfo=UTC))


def test_tampered_member_hash_fails_closed(tmp_path) -> None:
    source = tmp_path / "source.json"
    output = tmp_path / "cohort.json"
    write_trace(_trace("project-a", "signal-a"), source)
    manifest = build_trace_cohort([str(source)], cohort_id="cohort-1",
                                  assembled_by="reviewer", assembled_at=datetime(2026, 2, 1, tzinfo=UTC))
    payload = manifest.as_dict()
    payload["trace_refs"][0]["trace_hash"] = "f" * 64
    output.write_text(__import__("json").dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="trace cohort hash mismatch"):
        load_trace_cohort(output)
