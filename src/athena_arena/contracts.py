"""Immutable, domain-neutral contracts for Athena Arena V0."""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from math import isfinite
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable


def _norm(v: Any) -> Any:
    if isinstance(v, StrEnum):
        return v.value
    if isinstance(v, datetime):
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("timestamps must be timezone-aware")
        return v.isoformat()
    if is_dataclass(v):
        return {f.name: _norm(getattr(v, f.name)) for f in fields(v)}
    if isinstance(v, Mapping):
        return {str(k): _norm(v[k]) for k in sorted(v, key=str)}
    if isinstance(v, (tuple, list)):
        return [_norm(x) for x in v]
    if isinstance(v, (set, frozenset)):
        return sorted(
            (_norm(x) for x in v),
            key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")),
        )
    if isinstance(v, float):
        if not isfinite(v):
            raise ValueError("non-finite float")
        return v
    if v is None or isinstance(v, (str, int, bool)):
        return v
    raise TypeError(f"unsupported canonical value {type(v).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(_norm(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


class PopulationState(StrEnum):
    SEED = "SEED"
    SHADOW = "SHADOW"
    INCUMBENT = "INCUMBENT"
    CANDIDATE = "CANDIDATE"
    QUARANTINE = "QUARANTINE"
    PROMOTED = "PROMOTED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"
    REJECTED = "REJECTED"
    GRAVEYARD = "GRAVEYARD"


class MutationType(StrEnum):
    PARAMETER = "PARAMETER"
    COMPONENT = "COMPONENT"
    BEHAVIORAL = "BEHAVIORAL"
    CROSSOVER = "CROSSOVER"


class GauntletResult(StrEnum):
    PROMOTE = "PROMOTE"
    QUARANTINE = "QUARANTINE"
    REJECT = "REJECT"
    MORE_EVIDENCE = "MORE_EVIDENCE"


@dataclass(frozen=True)
class DecisionProposal:
    action: str
    timestamp: datetime
    confidence: float = 0.0
    reason: str = ""
    features: Mapping[str, Any] = field(default_factory=dict)
    policy_id: str = ""

    def __post_init__(self):
        if self.timestamp.tzinfo is None or not 0 <= self.confidence <= 1:
            raise ValueError("invalid decision proposal")
        object.__setattr__(self, "features", MappingProxyType(dict(self.features)))


@dataclass(frozen=True)
class ConstraintResult:
    allowed: bool
    violations: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class ExecutionRecord:
    execution_id: str
    proposal_id: str
    timestamp: datetime
    executed: bool
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


@dataclass(frozen=True)
class OutcomeRecord:
    outcome_id: str
    execution_id: str
    timestamp: datetime
    reward: float | None = None
    metrics: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        if any(not isfinite(x) for x in self.metrics.values()):
            raise ValueError("metrics must be finite")
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))


@dataclass(frozen=True)
class FitnessValue:
    value: float | None
    measured: bool = True
    evidence_ids: tuple[str, ...] = ()
    note: str = ""

    def __post_init__(self):
        if self.value is not None and not isfinite(self.value):
            raise ValueError("fitness must be finite")
        if not self.measured and self.value is not None:
            raise ValueError("unavailable fitness cannot have a value")


@dataclass(frozen=True)
class FitnessVector:
    dimensions: Mapping[str, FitnessValue]
    partition: str = ""

    def __post_init__(self):
        object.__setattr__(self, "dimensions", MappingProxyType(dict(self.dimensions)))

    def get(self, name: str) -> FitnessValue:
        return self.dimensions.get(name, FitnessValue(None, False, note="unavailable"))

    @property
    def hash(self):
        return canonical_hash(self)


@dataclass(frozen=True)
class LineageEvent:
    event_id: str
    timestamp: datetime
    event_type: str
    policy_id: str
    parent_policy_ids: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)
    previous_hash: str = ""
    record_hash: str = ""

    def __post_init__(self):
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


@dataclass(frozen=True)
class PolicyProjection:
    """Arena lifecycle projection; never an execution-authority grant."""

    policy_id: str
    population_state: PopulationState
    gauntlet_state: str = ""
    execution_authority: bool = False

    def __post_init__(self):
        if self.execution_authority:
            raise ValueError("Arena V0 cannot grant execution authority")


@dataclass(frozen=True)
class PromotionDecision:
    policy_id: str
    result: GauntletResult
    reason: str
    gauntlet_ref: str = ""
    evidence_ids: tuple[str, ...] = ()
    decided_at: datetime | None = None


@dataclass(frozen=True)
class ExperimentManifest:
    experiment_id: str
    created_at: datetime
    source_commit: str = ""
    dataset_refs: Mapping[str, str] = field(default_factory=dict)
    seed: int = 0
    policy_refs: Mapping[str, str] = field(default_factory=dict)
    mutation_refs: Mapping[str, str] = field(default_factory=dict)
    config: Mapping[str, Any] = field(default_factory=dict)
    gauntlet_ref: str = ""
    runtime_versions: Mapping[str, str] = field(default_factory=dict)
    artifact_hashes: Mapping[str, str] = field(default_factory=dict)

    _PROXIED_FIELDS = (
        "dataset_refs", "policy_refs", "mutation_refs", "config",
        "runtime_versions", "artifact_hashes",
    )

    def __post_init__(self):
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        for name in self._PROXIED_FIELDS:
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    @property
    def hash(self):
        return canonical_hash(self)


@runtime_checkable
class PolicyRuntime(Protocol):
    def decide(self, state: Any) -> DecisionProposal: ...


@runtime_checkable
class DomainAdapter(Protocol):
    def get_state(self, timestamp: datetime) -> Any: ...
    def validate_action(self, proposal: DecisionProposal) -> ConstraintResult: ...
    def execute_shadow(self, proposal: DecisionProposal) -> ExecutionRecord: ...
    def observe_outcome(self, execution: ExecutionRecord) -> OutcomeRecord: ...
    def calculate_domain_metrics(
        self, decision: DecisionProposal, outcome: OutcomeRecord,
    ) -> Mapping[str, float]: ...
