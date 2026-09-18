from datetime import UTC, datetime

import pytest

from athena_procurement_arena import (
    SignalType,
    accept_candidate,
    candidate_from_capture,
    capture_markdown,
)


def _capture():
    return capture_markdown(
        "https://example.com/orla", "Project approval occurred on 2026-01-14.",
        capture_id="capture-1", captured_by="operator",
        captured_at=datetime(2026, 9, 18, tzinfo=UTC),
    )


def test_candidate_requires_exact_quote_and_acceptance_preserves_binding():
    capture = _capture()
    candidate = candidate_from_capture(
        capture, candidate_id="candidate-1", project_id="south-railroad",
        observed_at=datetime(2026, 1, 14, tzinfo=UTC), signal_type=SignalType.CONSTRUCTION_APPROVED,
        title="Construction approval", source_quote="Project approval occurred on 2026-01-14.",
        claims={"power_need": "onsite generation"}, proposed_by="reviewer",
    )
    signal = accept_candidate(candidate, capture, signal_id="signal-1", reviewed_by="reviewer",
                              reviewed_at=datetime(2026, 9, 18, tzinfo=UTC))
    assert signal.source_sha256 == capture.content_sha256
    assert signal.source_quote == candidate.source_quote
    assert signal.claims["candidate_hash"] == candidate.candidate_hash


def test_candidate_rejects_quote_not_in_capture():
    with pytest.raises(ValueError, match="exact span"):
        candidate_from_capture(
            _capture(), candidate_id="candidate-2", project_id="south-railroad",
            observed_at=datetime(2026, 1, 14, tzinfo=UTC), signal_type=SignalType.PERMIT_APPROVED,
            title="Permit", source_quote="not present", claims={}, proposed_by="reviewer",
        )


def test_acceptance_rejects_different_capture():
    capture = _capture()
    candidate = candidate_from_capture(
        capture, candidate_id="candidate-3", project_id="south-railroad",
        observed_at=datetime(2026, 1, 14, tzinfo=UTC), signal_type=SignalType.POWER_REQUIREMENT,
        title="Power", source_quote="Project approval occurred on 2026-01-14.", claims={}, proposed_by="reviewer",
    )
    other = capture_markdown("https://example.com/other", "different", capture_id="capture-2", captured_by="operator")
    with pytest.raises(ValueError, match="not bound"):
        accept_candidate(candidate, other, signal_id="signal-3", reviewed_by="reviewer")
