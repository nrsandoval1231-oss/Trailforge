"""Foundation contracts for the Procurement Arena.

This module is deliberately simulation-only. It contains no network, broker,
submission, or execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping

from athena_arena.contracts import canonical_hash


class AvailabilityError(ValueError):
    """Evidence is not valid at the requested point in time."""


class InvariantViolation(ValueError):
    """A hard Arena invariant was violated."""


class ClaimBasis(StrEnum):
    REPORTED = "REPORTED"
    CALCULATED = "CALCULATED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class PowerScope(StrEnum):
    CONSTRUCTION = "CONSTRUCTION"
    COMMISSIONING = "COMMISSIONING"
    BRIDGE = "BRIDGE"
    OPERATIONAL = "OPERATIONAL"
    BACKUP = "BACKUP"
    EMERGENCY = "EMERGENCY"
    DISPLACEMENT = "DISPLACEMENT"
    OTHER = "OTHER"


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True)
class EvidenceEvent:
    evidence_id: str
    source_id: str
    event_date: datetime
    document_date: datetime
    verified_available_at: datetime
    observed_at: datetime
    claims: Mapping[str, Any] = field(default_factory=dict)
    claim_basis: ClaimBasis = ClaimBasis.UNKNOWN
    source_version: str = ""
    lineage_family: str = ""
    is_prediction: bool = False

    def __post_init__(self) -> None:
        for name in ("event_date", "document_date", "verified_available_at", "observed_at"):
            _aware(getattr(self, name), name)
        if not self.evidence_id or not self.source_id:
            raise ValueError("evidence_id and source_id are required")
        object.__setattr__(self, "claims", dict(self.claims))

    def visible_at(self, simulation_time: datetime) -> bool:
        _aware(simulation_time, "simulation_time")
        return self.verified_available_at <= simulation_time and not self.is_prediction


@dataclass(frozen=True)
class PowerNeed:
    need_id: str
    scope: PowerScope
    start: datetime
    end: datetime
    required_mw: float
    dependable_supply_mw: float | None
    service_type: str = ""

    def __post_init__(self) -> None:
        _aware(self.start, "start")
        _aware(self.end, "end")
        if self.end <= self.start or self.required_mw < 0:
            raise ValueError("invalid power interval or load")
        if self.dependable_supply_mw is not None and self.dependable_supply_mw < 0:
            raise ValueError("dependable supply cannot be negative")


@dataclass(frozen=True)
class Supply:
    start: datetime
    end: datetime
    dependable_mw: float | None
    source_id: str = ""

    def __post_init__(self) -> None:
        _aware(self.start, "start")
        _aware(self.end, "end")
        if self.end <= self.start or (self.dependable_mw is not None and self.dependable_mw < 0):
            raise ValueError("invalid supply interval")


def calculate_power_gap(need: PowerNeed, supplies: tuple[Supply, ...] = ()) -> dict[str, Any]:
    """Calculate a conservative gap; unknown supply remains explicitly unknown."""
    relevant = [s for s in supplies if s.start < need.end and need.start < s.end]
    if need.dependable_supply_mw is None or any(s.dependable_mw is None for s in relevant):
        return {"status": "UNKNOWN", "peak_gap_mw": None, "need_id": need.need_id}
    supply = max((s.dependable_mw for s in relevant), default=need.dependable_supply_mw)
    gap = max(0.0, need.required_mw - supply)
    return {"status": "GAP" if gap else "NO_GAP", "peak_gap_mw": gap, "need_id": need.need_id}


def validate_power_scopes(needs: tuple[PowerNeed, ...]) -> None:
    """Reject overlapping intervals in the same scope to prevent double count."""
    for index, left in enumerate(needs):
        for right in needs[index + 1:]:
            if left.scope == right.scope and left.start < right.end and right.start < left.end:
                raise InvariantViolation("I-12 overlapping power scope double count")


@dataclass(frozen=True)
class GroundTruth:
    procurement_episode_id: str
    outcome: str
    solicitation_at: datetime | None = None


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    version: str
    seed: int
    timeline: tuple[datetime, ...]
    evidence: tuple[EvidenceEvent, ...]
    truth: GroundTruth
    tenant_id: str = "default"


def validate_scenario(scenario: Scenario) -> str:
    """Validate structural and temporal invariants and return a stable hash."""
    if not scenario.scenario_id or not scenario.version or not isinstance(scenario.seed, int):
        raise ValueError("scenario_id, version, and integer seed are required")
    if not scenario.timeline:
        raise ValueError("scenario timeline cannot be empty")
    for timestamp in scenario.timeline:
        _aware(timestamp, "timeline timestamp")
    if tuple(sorted(scenario.timeline)) != scenario.timeline:
        raise ValueError("timeline must be sorted")
    if len({item.evidence_id for item in scenario.evidence}) != len(scenario.evidence):
        raise InvariantViolation("duplicate evidence id")
    if any(item.is_prediction for item in scenario.evidence):
        raise InvariantViolation("I-02 prediction-as-evidence")
    if scenario.truth.solicitation_at is not None:
        _aware(scenario.truth.solicitation_at, "solicitation_at")
    return canonical_hash(scenario)


@dataclass(frozen=True)
class FrozenDecision:
    scenario_id: str
    simulation_time: datetime
    policy_id: str
    visible_evidence_ids: tuple[str, ...]
    forecast: Mapping[str, Any]
    action: str
    previous_hash: str = ""
    record_hash: str = ""

    def __post_init__(self) -> None:
        _aware(self.simulation_time, "simulation_time")
        object.__setattr__(self, "forecast", dict(self.forecast))


class FrozenDecisionLedger:
    """Append-only hash chain; callers receive detached frozen snapshots."""

    def __init__(self) -> None:
        self._records: list[FrozenDecision] = []

    @property
    def records(self) -> tuple[FrozenDecision, ...]:
        return tuple(self._records)

    @property
    def head_hash(self) -> str:
        return self._records[-1].record_hash if self._records else ""

    def append(self, decision: FrozenDecision) -> FrozenDecision:
        if decision.record_hash:
            raise InvariantViolation("cannot append an already-hashed decision")
        detached = replace(decision, previous_hash=self.head_hash)
        payload = {f.name: getattr(detached, f.name) for f in fields(detached) if f.name != "record_hash"}
        detached = replace(detached, record_hash=canonical_hash(payload))
        self._records.append(detached)
        return detached

    def verify(self) -> bool:
        previous = ""
        for item in self._records:
            if item.previous_hash != previous:
                return False
            payload = {f.name: getattr(item, f.name) for f in fields(item) if f.name != "record_hash"}
            if item.record_hash != canonical_hash(payload):
                return False
            previous = item.record_hash
        return True
