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
    assert parent_only.reason_codes == ("REQUIRED_CAPACITY_NOT_CAPTURED",)
    assert missing_fuel.status == AuraRfpScreenStatus.NEEDS_REVIEW
    assert missing_fuel.reason_codes == ("FUEL_REQUIREMENT_NOT_CAPTURED",)
