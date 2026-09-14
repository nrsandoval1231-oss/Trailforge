import json

import pytest

from athena_procurement_arena import (
    AuraRfpScreenStatus,
    CaptureRequest,
    build_candidate_bundle,
    capture_listing,
    current_target_fixtures,
    load_bundle,
)

EXCERPT = (
    "Contractor shall furnish temporary generation for construction and "
    "commissioning loads of 750 kW during the interconnection delay."
)


def _request(**overrides):
    base = dict(
        fixture_id="GT-099",
        source_url="https://example-city.gov/bids/tempgen",
        excerpt=EXCERPT,
        buyer="Example County",
        scope="temporary power for construction and commissioning",
        published_at="2026-09-02T09:00:00-05:00",
        retrieved_at="2026-09-14T08:00:00-05:00",
        verified_by="reviewer-2026-09-14",
        verification_notes="Official bid page reviewed.",
        lifecycle="OPEN",
        required_kw=750,
        fuel="natural gas",
    )
    base.update(overrides)
    return CaptureRequest(**base)


def test_captured_listing_reaches_the_shortlist_through_the_normal_gate():
    """A captured record must flow through the same path as a checked-in bundle."""
    bundle = build_candidate_bundle(_request())
    assert current_target_fixtures(bundle) == bundle.fixtures


def test_capture_screens_immediately_and_reports_the_verdict():
    result = capture_listing(_request())
    assert result["screen"]["status"] == AuraRfpScreenStatus.QUALIFIED
    assert result["screen"]["required_kw"] == 750
    assert result["shortlisted"] is True
    assert result["written"] is None


def test_capture_is_deterministic_and_round_trips_through_the_loader(tmp_path):
    destination = tmp_path / "candidate.json"
    first = capture_listing(_request(), out_path=destination)
    written = destination.read_text(encoding="utf-8")
    second = capture_listing(_request(), out_path=destination)

    assert first["source_sha256"] == second["source_sha256"]
    assert written == destination.read_text(encoding="utf-8")
    reloaded = load_bundle(destination)
    assert reloaded.fixtures[0].fixture_id == "GT-099"
    assert json.loads(written)["schema_version"] == "procurement-arena-fixture-bundle-v1"


def test_uncaptured_capacity_is_not_invented():
    """Omitting a field must not silently produce a qualifying record."""
    result = capture_listing(_request(required_kw=None))
    assert result["screen"]["status"] == AuraRfpScreenStatus.NEEDS_REVIEW
    assert result["screen"]["reason_codes"] == ["REQUIRED_CAPACITY_NOT_CAPTURED"]
    assert result["shortlisted"] is False


def test_non_current_lifecycle_stays_out_of_the_shortlist():
    result = capture_listing(_request(lifecycle="CLOSED"))
    assert result["screen"]["status"] == AuraRfpScreenStatus.QUALIFIED
    assert result["current"] is False
    assert result["shortlisted"] is False


def test_naive_timestamps_and_empty_fields_are_rejected():
    with pytest.raises(ValueError, match="UTC offset"):
        build_candidate_bundle(_request(published_at="2026-09-02T09:00:00"))
    with pytest.raises(ValueError, match="closes_at must follow"):
        build_candidate_bundle(_request(closes_at="2026-08-01T09:00:00-05:00"))
    with pytest.raises(ValueError, match="missing required capture fields"):
        build_candidate_bundle(_request(verified_by="   "))
