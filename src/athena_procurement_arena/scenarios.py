"""Named scenario-family registry for synthetic campaign generation."""
from __future__ import annotations

SCENARIO_FAMILIES = (
    "capital_plan_funded_rfp", "funding_denied", "deferred", "permit_engineering_procurement",
    "permit_cancelled", "expiration_recompete", "extension_later_recompete", "direct_renewal",
    "failed_solicitation_rebid", "failed_cancelled", "recurring_buyer", "false_recurrence_amendments",
    "cross_project_future_procurement", "cross_project_unrelated", "epc_procurement", "gc_bid_room",
    "public_rfp", "private_rfq", "sole_source_direct", "cooperative_route", "utility_delay_bridge",
    "service_on_time", "commissioning_power", "replacement_temporary_generation", "replacement_no_rental",
    "standby_no_temporary_need", "emergency_rental", "rename", "ownership_transfer", "phase_split",
    "multi_site", "bundled_epc", "generic_title_hidden_scope", "buried_addendum_requirement",
    "amendment_changes_requirement", "award_supplemental_need", "duplicate_reporting",
    "contradictory_authorities", "unknown_supply", "partial_supply",
)

def family_scenario(name: str, seed: int):
    """Return a deterministic runnable template for any registered family."""
    from dataclasses import replace
    from .campaign import synthetic_scenario
    if name not in SCENARIO_FAMILIES:
        raise KeyError(f"unknown scenario family: {name}")
    base = synthetic_scenario(seed)
    evidence = tuple(replace(item, claims={"family": name, "signal": item.claims}) for item in base.evidence)
    return replace(base, scenario_id=f"{name}-{seed}", evidence=evidence)

def validate_family_registry() -> tuple[str, ...]:
    if len(SCENARIO_FAMILIES) != 40 or len(set(SCENARIO_FAMILIES)) != 40:
        raise ValueError("scenario registry must contain exactly 40 unique families")
    return SCENARIO_FAMILIES
