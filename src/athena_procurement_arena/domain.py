"""Immutable typed domain contracts for Trailforge procurement research."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from .foundation import PowerScope, _aware


class OrganizationRole(StrEnum):
    OWNER = "OWNER"
    DEVELOPER = "DEVELOPER"
    BUYER = "BUYER"
    UTILITY = "UTILITY"
    EPC = "EPC"
    GC = "GC"
    ENGINEER = "ENGINEER"
    SUPPLIER = "SUPPLIER"


class ProcurementState(StrEnum):
    UNKNOWN = "UNKNOWN"
    EARLY_SIGNAL = "EARLY_SIGNAL"
    PROGRAM = "PROGRAM"
    PROJECT_CONFIRMED = "PROJECT_CONFIRMED"
    FUNDED = "FUNDED"
    ENGINEERING = "ENGINEERING"
    PROCUREMENT_WATCH = "PROCUREMENT_WATCH"
    PRE_SOLICITATION = "PRE_SOLICITATION"
    SOLICITATION_RELEASED = "SOLICITATION_RELEASED"
    PRIVATE_PROCUREMENT = "PRIVATE_PROCUREMENT"
    DIRECT_AWARD = "DIRECT_AWARD"
    EXTENDED = "EXTENDED"
    DEFERRED = "DEFERRED"
    CANCELLED = "CANCELLED"
    AWARDED = "AWARDED"
    FAILED = "FAILED"
    REBID_EXPECTED = "REBID_EXPECTED"
    CLOSED = "CLOSED"


class CustomerAction(StrEnum):
    IGNORE = "IGNORE"
    WATCH = "WATCH"
    RESEARCH = "RESEARCH"
    PREPARE = "PREPARE"
    ENGAGE = "ENGAGE"
    RESOLVE_BLOCKER = "RESOLVE_BLOCKER"
    BID_REVIEW = "BID_REVIEW"
    READY_FOR_AUTHORIZED_SUBMISSION = "READY_FOR_AUTHORIZED_SUBMISSION"


class ReadinessStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class Organization:
    organization_id: str
    name: str
    roles: tuple[OrganizationRole, ...]


@dataclass(frozen=True)
class Site:
    site_id: str
    name: str
    geography: str = ""


@dataclass(frozen=True)
class CapitalProgram:
    program_id: str
    name: str
    owner_id: str


@dataclass(frozen=True)
class Project:
    project_id: str
    program_id: str
    owner_id: str
    site_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectPhase:
    phase_id: str
    project_id: str
    name: str
    start: datetime | None = None
    end: datetime | None = None

    def __post_init__(self):
        if self.start: _aware(self.start, "start")
        if self.end: _aware(self.end, "end")
        if self.start and self.end and self.end <= self.start:
            raise ValueError("phase end must follow start")


@dataclass(frozen=True)
class ProcurementEpisode:
    procurement_episode_id: str
    project_id: str
    buyer_id: str
    state: ProcurementState = ProcurementState.UNKNOWN
    state_since: datetime | None = None


@dataclass(frozen=True)
class Solicitation:
    solicitation_id: str
    procurement_episode_id: str
    route: str
    release_at: datetime | None = None
    deadline: datetime | None = None


@dataclass(frozen=True)
class TrailState:
    project_id: str
    phase_id: str | None
    procurement_episode_id: str | None
    state: ProcurementState
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProcurementForecast:
    state: ProcurementState
    confidence: float
    expected_at: datetime | None = None

    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class PowerForecast:
    scope: PowerScope
    status: str
    peak_gap_mw: float | None
    start: datetime | None = None
    end: datetime | None = None


@dataclass(frozen=True)
class ActionDecision:
    action: CustomerAction
    reason_codes: tuple[str, ...] = ()
    readiness: dict[str, ReadinessStatus] | None = None

    def __post_init__(self):
        if self.readiness is not None and any(not isinstance(value, ReadinessStatus) for value in self.readiness.values()):
            raise ValueError("readiness values must use ReadinessStatus")

    @property
    def has_mandatory_failure(self) -> bool:
        return any(value == ReadinessStatus.FAIL for value in (self.readiness or {}).values())
