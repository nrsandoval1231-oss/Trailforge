from datetime import UTC, datetime

import pytest

from athena_procurement_arena import BaselineA, capture_prospective_shadow
from athena_procurement_arena.campaign import synthetic_scenario


def test_prospective_shadow_capture_is_reproducible_and_outcome_free():
    captured_at = datetime(2026, 9, 14, tzinfo=UTC)
    kwargs = {
        "record_id": "shadow-1", "captured_at": captured_at,
        "source_url": "https://example.com/record", "source_sha256": "a" * 64,
        "verified_by": "human-reviewer", "scenario": synthetic_scenario(8),
        "policy_id": "BASELINE_A", "policy": BaselineA(),
    }
    first = capture_prospective_shadow(**kwargs)
    second = capture_prospective_shadow(**kwargs)
    assert first.record_hash == second.record_hash
    assert first.execution_authority == "ABSENT"
    assert "outcome" not in first.manifest and "verified_outcome" not in first.manifest


def test_prospective_shadow_capture_fails_closed_for_bad_provenance_or_known_outcome():
    kwargs = {
        "record_id": "shadow-1", "captured_at": datetime(2026, 9, 14, tzinfo=UTC),
        "source_url": "https://example.com/record", "source_sha256": "a" * 64,
        "verified_by": "human-reviewer", "scenario": synthetic_scenario(8),
        "policy_id": "BASELINE_A", "policy": BaselineA(),
    }
    with pytest.raises(ValueError, match="known outcome"):
        capture_prospective_shadow(**kwargs, known_outcome="AWARDED")
    with pytest.raises(ValueError, match="64-character"):
        capture_prospective_shadow(**(kwargs | {"source_sha256": "not-a-digest"}))
