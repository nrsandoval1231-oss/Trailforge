from datetime import UTC, datetime

from athena_procurement_arena import (
    AuraRfpScreenStatus,
    EvidenceEvent,
    screen_aura_rental_candidate,
)


def _evidence(claims):
    timestamp = datetime(2026, 9, 11, tzinfo=UTC)
    return (EvidenceEvent("e-1", "manual-source", timestamp, timestamp, timestamp, timestamp, claims),)


def test_planned_commissioning_power_can_qualify_without_prime_keyword():
    result = screen_aura_rental_candidate(_evidence({
        "commissioning_scope": "planned temporary power during energization",
        "required_kw": 500,
        "primary_fuel": "natural gas",
    }))
    assert result.status == AuraRfpScreenStatus.QUALIFIED
    assert result.required_kw == 500


def test_emergency_and_permanent_capacity_patterns_are_rejected_first():
    emergency = screen_aura_rental_candidate(_evidence({
        "temporary_scope": "generator outage contingency response",
        "required_kw": 500,
        "primary_fuel": "propane",
    }))
    permanent = screen_aura_rental_candidate(_evidence({
        "commissioning_scope": "temporary power",
        "required_mw": 3,
        "primary_fuel": "natural gas",
        "contract": "power purchase agreement capacity product",
    }))
    assert emergency.reason_codes == ("EMERGENCY_OR_CONTINGENCY_SCOPE",)
    assert permanent.reason_codes == ("PERMANENT_CAPACITY_OR_PPA_SCOPE",)


def test_parent_capacity_and_missing_fuel_stay_out_of_shortlist():
    parent_only = screen_aura_rental_candidate(_evidence({
        "construction_scope": "planned bridge power",
        "facility_capacity_mw": 300,
        "primary_fuel": "natural gas",
    }))
    missing_fuel = screen_aura_rental_candidate(_evidence({
        "temporary_scope": "planned commissioning power",
        "required_kw": 500,
    }))
    assert parent_only.status == AuraRfpScreenStatus.NEEDS_REVIEW
    assert parent_only.reason_codes == (
        "REQUIRED_CAPACITY_NOT_CAPTURED",
        "CAPACITY_EVIDENCE_IS_RATING_OR_AGGREGATE_ONLY",
    )
    assert parent_only.required_kw is None
    assert missing_fuel.status == AuraRfpScreenStatus.NEEDS_REVIEW
    assert missing_fuel.reason_codes == ("FUEL_REQUIREMENT_NOT_CAPTURED",)


def test_program_aggregate_capacity_cannot_satisfy_the_minimum():
    """A multi-project program total is not per-project requirement evidence."""
    aggregate = screen_aura_rental_candidate(_evidence({
        "commissioning_scope": "planned temporary generation program",
        "program_mw": 400,
        "primary_fuel": "natural gas",
    }))
    assert aggregate.status == AuraRfpScreenStatus.NEEDS_REVIEW
    assert "CAPACITY_EVIDENCE_IS_RATING_OR_AGGREGATE_ONLY" in aggregate.reason_codes
    assert aggregate.required_kw is None


def test_equipment_rating_cannot_satisfy_the_minimum():
    """A generator nameplate rating is not evidence of the load to be served."""
    rating_only = screen_aura_rental_candidate(_evidence({
        "construction_scope": "planned bridge power",
        "generator_kw": 2000,
        "primary_fuel": "natural gas",
    }))
    assert rating_only.status == AuraRfpScreenStatus.NEEDS_REVIEW
    assert rating_only.reason_codes == (
        "REQUIRED_CAPACITY_NOT_CAPTURED",
        "CAPACITY_EVIDENCE_IS_RATING_OR_AGGREGATE_ONLY",
    )


def test_stated_requirement_still_qualifies_alongside_a_rating():
    """A captured requirement governs even when a rating is also recorded."""
    both = screen_aura_rental_candidate(_evidence({
        "construction_scope": "planned bridge power",
        "construction_kw": 750,
        "generator_kw": 2000,
        "primary_fuel": "natural gas",
    }))
    assert both.status == AuraRfpScreenStatus.QUALIFIED
    assert both.required_kw == 750


def test_planned_outage_continuity_generation_is_not_emergency_scope():
    result = screen_aura_rental_candidate(
        _evidence(
            {
                "temporary_scope": "Planned temporary generation for switchgear replacement during a scheduled outage",
                "required_kw": 500,
                "primary_fuel": "natural gas",
            }
        )
    )
    assert result.status == AuraRfpScreenStatus.QUALIFIED


def test_unplanned_outage_response_remains_rejected():
    result = screen_aura_rental_candidate(
        _evidence(
            {
                "temporary_scope": "temporary generation during an unplanned outage",
                "required_kw": 500,
                "primary_fuel": "natural gas",
            }
        )
    )
    assert result.status == AuraRfpScreenStatus.REJECTED


def test_infinite_capacity_is_unknown_instead_of_qualified():
    for capacity in (float("inf"), "inf", "Infinity"):
        result = screen_aura_rental_candidate(
            _evidence(
                {
                    "temporary_scope": "planned construction temporary power",
                    "required_kw": capacity,
                    "primary_fuel": "natural gas",
                }
            )
        )
        assert result.status == AuraRfpScreenStatus.NEEDS_REVIEW
        assert result.required_kw is None


def test_scheduled_outage_mention_does_not_hide_emergency_outage_scope():
    result = screen_aura_rental_candidate(
        _evidence(
            {
                "temporary_scope": "temporary generation for a scheduled outage and an unplanned outage",
                "required_kw": 500,
                "primary_fuel": "natural gas",
            }
        )
    )
    assert result.status == AuraRfpScreenStatus.REJECTED


def test_mw_conversion_overflow_is_not_a_supported_capacity():
    result = screen_aura_rental_candidate(
        _evidence(
            {
                "temporary_scope": "planned construction temporary power",
                "required_mw": 1e308,
                "primary_fuel": "natural gas",
            }
        )
    )
    assert result.status == AuraRfpScreenStatus.NEEDS_REVIEW
    assert result.required_kw is None
