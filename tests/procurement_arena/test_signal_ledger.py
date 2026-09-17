from datetime import UTC, datetime, timedelta

import pytest

from athena_procurement_arena import (
    EvidenceClass,
    ProjectSignal,
    SignalType,
    load_trace,
    trace_project_signals,
    write_trace,
)


def _signal(signal_id, project_id="p-1", *, days=0, evidence_class=EvidenceClass.PUBLIC,
            source_ref=None, source_url=None):
    return ProjectSignal(
        signal_id=signal_id,
        project_id=project_id,
        observed_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=days),
        signal_type=SignalType.POWER_REQUIREMENT,
        title="Power requirement identified",
        evidence_class=evidence_class,
        source_url=source_url if source_url is not None else (
            "https://example.com/source" if evidence_class == EvidenceClass.PUBLIC else None
        ),
        source_ref=source_ref,
        source_sha256="a" * 64,
        verified_by="reviewer",
        claims={"required_kw": 7096},
    )


def test_trace_sorts_and_identifies_earliest_signal():
    traces = trace_project_signals([_signal("later", days=2), _signal("first"), _signal("other", "p-2")])
    assert [trace.project_id for trace in traces] == ["p-1", "p-2"]
    assert traces[0].earliest_signal.signal_id == "first"
    assert traces[0].signals[-1].signal_id == "later"


def test_public_and_confidential_evidence_require_separate_provenance():
    private = _signal("private", evidence_class=EvidenceClass.CONFIDENTIAL, source_ref="local://waterleaf/sow.pdf")
    assert private.source_url is None
    with pytest.raises(ValueError, match=r"HTTP\(S\)"):
        _signal("bad", source_url="local://not-public")
    with pytest.raises(ValueError, match="source_ref"):
        _signal("missing", evidence_class=EvidenceClass.CONFIDENTIAL)


def test_trace_json_round_trip_preserves_hash(tmp_path):
    trace = trace_project_signals([_signal("one")])[0]
    path = tmp_path / "trace.json"
    write_trace(trace, path)
    loaded = load_trace(path)
    assert loaded.trace_hash == trace.trace_hash
    assert loaded.earliest_signal.as_dict() == trace.earliest_signal.as_dict()


def test_trace_rejects_tampered_hash(tmp_path):
    trace = trace_project_signals([_signal("one")])[0]
    path = tmp_path / "trace.json"
    write_trace(trace, path)
    raw = path.read_text(encoding="utf-8").replace(trace.trace_hash, "b" * 64)
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_trace(path)
