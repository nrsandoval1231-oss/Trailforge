"""Fail-closed manual RFP intake for 2G Aura rental fit screening.

This module evaluates already-captured, source-backed evidence only.  It has no
network, solicitation, outreach, pricing, or submission capability.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Any

from .foundation import EvidenceEvent


class AuraRfpScreenStatus(StrEnum):
    QUALIFIED = "QUALIFIED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass(frozen=True)
class AuraRfpScreen:
    """Auditable outcome of a product-fit screen, never a bid recommendation."""

    status: AuraRfpScreenStatus
    reason_codes: tuple[str, ...]
    required_kw: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "required_kw": self.required_kw,
        }


_PLANNED_SCOPE_TERMS = (
    "temporary", "construction", "commissioning", "energization", "startup",
    "bridge power", "grid delay", "utility delay",
)
_EMERGENCY_TERMS = (
    "emergency", "contingency", "psps", "storm", "restoration", "blackout",
)
_PERMANENT_TERMS = (
    "power purchase agreement", "ppa", "tolling agreement", "capacity product",
    "long-term capacity", "long term capacity", "own operate maintain", "own, operate and maintain",
)
_MAINTENANCE_TERMS = ("maintenance", "maintain", "repair", "service")
_FUEL_FIELDS = frozenset({"fuel", "fuel_type", "primary_fuel", "required_fuel", "fuel_requirement"})

# Fields that state what the opportunity actually requires.  Only these can
# satisfy the minimum-capacity gate.
_REQUIREMENT_KW_FIELDS = frozenset({
    "required_kw", "temporary_kw", "commissioning_kw", "construction_kw", "bridge_kw",
})
_REQUIREMENT_MW_FIELDS = frozenset({
    "required_mw", "temporary_mw", "commissioning_mw", "construction_mw", "bridge_mw",
})

# Fields that describe equipment ratings, parent facility nameplate, or program
# aggregates.  They are recorded but never substituted for a stated requirement:
# a 400 MW multi-project program does not evidence a qualifying per-project load.
_RATING_KW_FIELDS = frozenset({"generator_kw", "prime_kw", "nameplate_kw", "standby_kw"})
_RATING_MW_FIELDS = frozenset({
    "generator_mw", "prime_mw", "nameplate_mw", "standby_mw",
    "facility_capacity_mw", "aggregate_mw", "program_mw", "total_mw",
})


def _claims(evidence: tuple[EvidenceEvent, ...]) -> tuple[Mapping[str, Any], ...]:
    return tuple(item.claims for item in evidence)


def _text(evidence: tuple[EvidenceEvent, ...]) -> str:
    return " ".join(f"{key} {value}" for claim in _claims(evidence) for key, value in claim.items()).lower()


def _capacity_kw(evidence: tuple[EvidenceEvent, ...], kw_fields: frozenset[str],
                 mw_fields: frozenset[str]) -> float | None:
    """Return the largest captured capacity in kW across the given field sets."""
    values: list[float] = []
    for claim in _claims(evidence):
        for key, value in claim.items():
            normalized = str(key).lower()
            if normalized not in kw_fields | mw_fields:
                continue
            if isinstance(value, bool):
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            capacity_kw = numeric * 1000 if normalized in mw_fields else numeric
            if isfinite(capacity_kw) and capacity_kw >= 0:
                values.append(capacity_kw)
    return max(values, default=None)


def _required_kw(evidence: tuple[EvidenceEvent, ...]) -> float | None:
    """Return the captured requirement only; ratings and aggregates never count."""
    return _capacity_kw(evidence, _REQUIREMENT_KW_FIELDS, _REQUIREMENT_MW_FIELDS)


def _rating_kw(evidence: tuple[EvidenceEvent, ...]) -> float | None:
    """Return captured equipment/facility/program capacity, which is not a requirement."""
    return _capacity_kw(evidence, _RATING_KW_FIELDS, _RATING_MW_FIELDS)


def _fuel_text(evidence: tuple[EvidenceEvent, ...]) -> str:
    return " ".join(
        str(value).lower()
        for claim in _claims(evidence)
        for key, value in claim.items()
        if str(key).lower() in _FUEL_FIELDS
    )


def screen_aura_rental_candidate(
    evidence: tuple[EvidenceEvent, ...], *, minimum_kw: float = 300,
) -> AuraRfpScreen:
    """Screen a manually captured RFP candidate without filling evidentiary gaps.

    Qualification requires explicit planned-power scope, an explicitly captured
    requirement at or above ``minimum_kw``, and natural-gas or propane fuel
    evidence.  Equipment ratings, parent-facility nameplate, and multi-project
    program aggregates are deliberately not substitutes for a stated
    commissioning/construction requirement.
    """
    text = _text(evidence)
    # A scheduled electrical outage is planned continuity scope, not disaster response.
    remaining_scope = re.sub(r"\b(?:planned|scheduled) outage\b", "", text)
    unplanned_outage = bool(re.search(r"\boutage\b", remaining_scope))
    if unplanned_outage or any(term in text for term in _EMERGENCY_TERMS):
        return AuraRfpScreen(AuraRfpScreenStatus.REJECTED, ("EMERGENCY_OR_CONTINGENCY_SCOPE",))
    if any(term in text for term in _PERMANENT_TERMS):
        return AuraRfpScreen(AuraRfpScreenStatus.REJECTED, ("PERMANENT_CAPACITY_OR_PPA_SCOPE",))

    planned_scope = any(term in text for term in _PLANNED_SCOPE_TERMS)
    if any(term in text for term in _MAINTENANCE_TERMS) and not planned_scope:
        return AuraRfpScreen(AuraRfpScreenStatus.REJECTED, ("MAINTENANCE_ONLY_SCOPE",))
    if not planned_scope:
        return AuraRfpScreen(AuraRfpScreenStatus.NEEDS_REVIEW, ("PLANNED_POWER_SCOPE_UNSUPPORTED",))

    required_kw = _required_kw(evidence)
    if required_kw is None:
        reason_codes = ("REQUIRED_CAPACITY_NOT_CAPTURED",)
        if _rating_kw(evidence) is not None:
            reason_codes += ("CAPACITY_EVIDENCE_IS_RATING_OR_AGGREGATE_ONLY",)
        return AuraRfpScreen(AuraRfpScreenStatus.NEEDS_REVIEW, reason_codes)
    if required_kw < minimum_kw:
        return AuraRfpScreen(
            AuraRfpScreenStatus.REJECTED,
            ("REQUIRED_CAPACITY_BELOW_MINIMUM",),
            required_kw,
        )

    fuel_text = _fuel_text(evidence)
    if any(term in fuel_text for term in ("diesel", "light fuel oil", "lfo")):
        return AuraRfpScreen(AuraRfpScreenStatus.REJECTED, ("INCOMPATIBLE_FUEL",), required_kw)
    if not any(term in fuel_text for term in ("natural gas", "cng", "propane", "lpg")):
        return AuraRfpScreen(AuraRfpScreenStatus.NEEDS_REVIEW, ("FUEL_REQUIREMENT_NOT_CAPTURED",), required_kw)
    return AuraRfpScreen(
        AuraRfpScreenStatus.QUALIFIED,
        ("PLANNED_POWER_SCOPE", "REQUIRED_CAPACITY_SUPPORTED", "FUEL_COMPATIBLE"),
        required_kw,
    )

