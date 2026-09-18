from datetime import UTC, datetime

import pytest

from athena_procurement_arena.identity_review import ProjectIdentityReview, resolve_traces
from athena_procurement_arena.signal_ledger import EvidenceClass, ProjectSignal, ProjectTrace, SignalType


def _signal(signal_id: str, project_id: str, day: int) -> ProjectSignal:
    return ProjectSignal(signal_id, project_id, datetime(2026, 1, day, tzinfo=UTC),
                         SignalType.FEASIBILITY_COMPLETE, signal_id, EvidenceClass.PUBLIC,
                         "0" * 64, "reviewer", {}, source_url="https://example.com/source")


def _review(*members: str) -> ProjectIdentityReview:
    return ProjectIdentityReview("identity-1", "canonical-project", members, EvidenceClass.PUBLIC,
                                "1" * 64, "The projects are the same.", "reviewer",
                                datetime(2026, 2, 1, tzinfo=UTC), "matching project and site details",
                                source_url="https://example.com/identity")


def test_explicit_review_merges_traces_and_binds_provenance() -> None:
    traces = [ProjectTrace("alias-a", (_signal("a", "alias-a", 1),)),
              ProjectTrace("alias-b", (_signal("b", "alias-b", 2),))]
    resolved = resolve_traces(traces, [_review("alias-a", "alias-b")])
    assert len(resolved) == 1
    assert resolved[0].project_id == "canonical-project"
    assert [signal.signal_id for signal in resolved[0].signals] == ["a", "b"]
    assert resolved[0].signals[0].claims["identity_review_id"] == "identity-1"


def test_conflicting_identity_reviews_fail_closed() -> None:
    with pytest.raises(ValueError, match="conflicting identity reviews"):
        resolve_traces([ProjectTrace("alias-a", (_signal("a", "alias-a", 1),))],
                       [_review("alias-a"), ProjectIdentityReview(
                           "identity-2", "other-project", ("alias-a",), EvidenceClass.PUBLIC,
                           "2" * 64, "Different.", "reviewer", datetime(2026, 2, 2, tzinfo=UTC),
                           "different evidence", source_url="https://example.com/other")])


def test_identity_evidence_requires_public_source() -> None:
    with pytest.raises(ValueError, match="public identity evidence"):
        ProjectIdentityReview("identity-1", "canonical", ("alias",), EvidenceClass.PUBLIC,
                              "1" * 64, "quote", "reviewer", datetime(2026, 2, 1, tzinfo=UTC),
                              "rationale")
