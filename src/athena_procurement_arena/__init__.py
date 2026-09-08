"""Deterministic, research-only Procurement Arena primitives."""

from .foundation import (
    AvailabilityError,
    EvidenceEvent,
    FrozenDecision,
    FrozenDecisionLedger,
    GroundTruth,
    IdentityResolution,
    InvariantViolation,
    PowerNeed,
    PowerScope,
    Scenario,
    Supply,
    calculate_power_gap,
    calculate_power_profile,
    validate_power_scopes,
    validate_recommended_action,
    deduplicate_evidence,
    resolve_identity,
    validate_scenario,
)
from .scenario_dsl import ScenarioDsl
from .world import TemporalWorld, WorldObservation
from .policies import BaselineA, PolicyContract, buyer_frequency, keyword_rfp, latest_event, seeded_random_eligible, static_weighted_score

__all__ = [
    "AvailabilityError", "EvidenceEvent", "FrozenDecision", "FrozenDecisionLedger",
    "GroundTruth", "IdentityResolution", "InvariantViolation", "PowerNeed", "PowerScope", "Scenario", "Supply",
    "calculate_power_gap", "calculate_power_profile", "deduplicate_evidence", "resolve_identity", "validate_power_scopes", "validate_recommended_action", "validate_scenario",
    "ScenarioDsl", "TemporalWorld", "WorldObservation",
    "BaselineA", "PolicyContract", "buyer_frequency", "keyword_rfp", "latest_event",
    "seeded_random_eligible", "static_weighted_score",
]
