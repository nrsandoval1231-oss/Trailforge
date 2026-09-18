from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from athena_procurement_arena.fixtures import current_target_fixtures, load_bundle
from athena_procurement_arena.rfp_candidate_capture import (
    accept_rfp_candidate,
    candidate_from_excerpt,
    load_rfp_candidate,
    write_accepted_rfp_bundle,
    write_rfp_candidate,
)
from athena_procurement_arena.rfp_intake import AuraRfpScreenStatus, screen_aura_rental_candidate

PUBLISHED = datetime(2026, 9, 1, tzinfo=UTC)
RETRIEVED = datetime(2026, 9, 2, tzinfo=UTC)
EXCERPT = "Buyer seeks 750 kW of propane temporary construction power."
QUOTE = "750 kW of propane temporary construction power"


def _candidate():
    return candidate_from_excerpt(
        excerpt=EXCERPT, candidate_id="rfp-001", source_url="https://example.com/rfp-001",
        source_quote=QUOTE, buyer="Example Buyer", scope="temporary construction power",
        published_at=PUBLISHED, retrieved_at=RETRIEVED, captured_by="operator-1", required_kw=750,
        fuel="propane", solicitation_number="RFP-001",
    )


def test_candidate_is_hash_bound_and_does_not_retain_raw_excerpt(tmp_path):
    candidate = _candidate()
    output = tmp_path / "candidate.json"
    write_rfp_candidate(candidate, output)

    raw = json.loads(output.read_text(encoding="utf-8"))
    assert raw["source_sha256"]
    assert raw["candidate_hash"] == candidate.candidate_hash
    assert EXCERPT not in output.read_text(encoding="utf-8")
    assert load_rfp_candidate(output) == candidate
    with pytest.raises(FileExistsError):
        write_rfp_candidate(candidate, output)


def test_candidate_requires_an_exact_quote_from_the_local_excerpt():
    with pytest.raises(ValueError, match="exact span"):
        candidate_from_excerpt(
            excerpt=EXCERPT, candidate_id="rfp-001", source_url="https://example.com/rfp-001",
            source_quote="invented requirement", buyer="Example Buyer", scope="temporary construction power",
            published_at=PUBLISHED, retrieved_at=RETRIEVED, captured_by="operator-1",
        )


def test_acceptance_requires_matching_excerpt_review_and_explicit_lifecycle(tmp_path):
    candidate = _candidate()
    with pytest.raises(ValueError, match="fixture_id"):
        accept_rfp_candidate(candidate, excerpt=EXCERPT, fixture_id="", reviewed_by="reviewer-1",
                             verification_notes="checked", opportunity_status="OPEN")
    with pytest.raises(ValueError, match="reviewed_by"):
        accept_rfp_candidate(candidate, excerpt=EXCERPT, fixture_id="fixture-001", reviewed_by="   ",
                             verification_notes="checked", opportunity_status="OPEN")
    with pytest.raises(ValueError, match="cannot be UNKNOWN"):
        accept_rfp_candidate(candidate, excerpt=EXCERPT, fixture_id="fixture-001", reviewed_by="reviewer-1",
                             verification_notes="checked", opportunity_status="UNKNOWN")
    with pytest.raises(ValueError, match="hash"):
        accept_rfp_candidate(candidate, excerpt="changed source", fixture_id="fixture-001", reviewed_by="reviewer-1",
                             verification_notes="checked", opportunity_status="OPEN")

    bundle = accept_rfp_candidate(
        candidate, excerpt=EXCERPT, fixture_id="fixture-001", reviewed_by="reviewer-1",
        verification_notes="Reviewer verified the source excerpt and lifecycle.", opportunity_status="OPEN",
    )
    fixture = bundle.fixtures[0]
    assert fixture.source_sha256 == candidate.source_sha256
    assert fixture.scenario.evidence[0].claims["rfp_candidate_hash"] == candidate.candidate_hash
    assert screen_aura_rental_candidate(fixture.scenario.evidence).status == AuraRfpScreenStatus.QUALIFIED
    assert current_target_fixtures(bundle) == (fixture,)

    output = tmp_path / "fixture.json"
    write_accepted_rfp_bundle(bundle, output)
    assert load_bundle(output).fixtures[0].fixture_id == "fixture-001"
    with pytest.raises(FileExistsError):
        write_accepted_rfp_bundle(bundle, output)


def test_tampered_candidate_json_fails_to_load(tmp_path):
    output = tmp_path / "candidate.json"
    write_rfp_candidate(_candidate(), output)
    raw = json.loads(output.read_text(encoding="utf-8"))
    raw["buyer"] = "Different Buyer"
    output.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        load_rfp_candidate(output)
