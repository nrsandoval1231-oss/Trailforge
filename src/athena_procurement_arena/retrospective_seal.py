"""Explicit retrospective outcome seals for reviewed project traces."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from athena_arena.contracts import canonical_hash

from .signal_ledger import EvidenceClass, ProjectTrace, SignalType


class TraceOutcomeState(StrEnum):
    OBSERVED = "OBSERVED"
    NOT_OBSERVED_BY_CUTOFF = "NOT_OBSERVED_BY_CUTOFF"
    INCONCLUSIVE = "INCONCLUSIVE"


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _digest(value: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value.lower()):
        raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
    return value.lower()


@dataclass(frozen=True)
class TraceOutcomeSeal:
    seal_id: str
    project_id: str
    trace_hash: str
    target_signal_type: SignalType
    cutoff_at: datetime
    outcome_state: TraceOutcomeState
    source_sha256: str
    source_quote: str
    reviewer_statement: str
    reviewed_by: str
    reviewed_at: datetime
    source_url: str | None = None
    source_ref: str | None = None
    target_signal_id: str | None = None

    def __post_init__(self) -> None:
        _aware(self.cutoff_at, "cutoff_at")
        _aware(self.reviewed_at, "reviewed_at")
        if not self.seal_id or not self.project_id or not self.trace_hash or not self.reviewed_by:
            raise ValueError("seal identity, project, trace hash, and reviewer are required")
        if not self.source_quote or not self.reviewer_statement:
            raise ValueError("source_quote and reviewer_statement are required")
        _digest(self.trace_hash)
        _digest(self.source_sha256)
        if not self.target_signal_id and self.outcome_state == TraceOutcomeState.OBSERVED:
            raise ValueError("observed outcome requires target_signal_id")
        if self.target_signal_id and self.outcome_state != TraceOutcomeState.OBSERVED:
            raise ValueError("target_signal_id is allowed only for observed outcomes")

    @property
    def seal_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "trailforge-trace-outcome-seal-v1",
            "seal_id": self.seal_id,
            "project_id": self.project_id,
            "trace_hash": self.trace_hash,
            "target_signal_type": self.target_signal_type,
            "target_signal_id": self.target_signal_id,
            "cutoff_at": self.cutoff_at.isoformat(),
            "outcome_state": self.outcome_state,
            "source_sha256": self.source_sha256,
            "source_url": self.source_url,
            "source_ref": self.source_ref,
            "source_quote": self.source_quote,
            "reviewer_statement": self.reviewer_statement,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat(),
            "seal_hash": self.seal_hash,
        }


def seal_trace_outcome(trace: ProjectTrace, *, seal_id: str, target_signal_type: SignalType,
                       cutoff_at: datetime, outcome_state: TraceOutcomeState,
                       source_sha256: str, source_quote: str, reviewer_statement: str,
                       reviewed_by: str, reviewed_at: datetime, evidence_class: EvidenceClass,
                       source_url: str | None = None, source_ref: str | None = None,
                       target_signal_id: str | None = None) -> TraceOutcomeSeal:
    """Create a seal only from explicit reviewer-supplied outcome evidence."""
    _aware(cutoff_at, "cutoff_at")
    if evidence_class == EvidenceClass.PUBLIC:
        if not source_url or not source_url.startswith(("https://", "http://")):
            raise ValueError("public outcome evidence requires an HTTP(S) source_url")
    elif not source_ref:
        raise ValueError("confidential outcome evidence requires a source_ref")
    targets = [signal for signal in trace.signals if signal.signal_type == target_signal_type]
    if outcome_state == TraceOutcomeState.OBSERVED:
        matches = [signal for signal in targets if signal.signal_id == target_signal_id]
        if not matches or matches[0].observed_at > cutoff_at:
            raise ValueError("observed target signal must exist in trace by cutoff")
    elif targets and any(signal.observed_at <= cutoff_at for signal in targets):
        raise ValueError("trace contains an observed target by cutoff")
    return TraceOutcomeSeal(seal_id, trace.project_id, trace.trace_hash, target_signal_type,
                            cutoff_at, outcome_state, source_sha256, source_quote,
                            reviewer_statement, reviewed_by, reviewed_at, source_url, source_ref,
                            target_signal_id)


def write_outcome_seal(seal: TraceOutcomeSeal, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"outcome seal output already exists: {destination}")
    destination.write_text(json.dumps(seal.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def load_outcome_seal(path: str | Path) -> TraceOutcomeSeal:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema_version") != "trailforge-trace-outcome-seal-v1":
        raise ValueError("unsupported trace outcome seal schema_version")
    seal = TraceOutcomeSeal(raw["seal_id"], raw["project_id"], raw["trace_hash"],
                            SignalType(raw["target_signal_type"]), datetime.fromisoformat(raw["cutoff_at"]),
                            TraceOutcomeState(raw["outcome_state"]), raw["source_sha256"],
                            raw["source_quote"], raw["reviewer_statement"], raw["reviewed_by"],
                            datetime.fromisoformat(raw["reviewed_at"]), raw.get("source_url"),
                            raw.get("source_ref"), raw.get("target_signal_id"))
    if raw.get("seal_hash") != seal.seal_hash:
        raise ValueError("trace outcome seal hash mismatch")
    return seal


@dataclass(frozen=True)
class RetrospectiveOutcomeCohort:
    cohort_id: str
    trace_cohort_hash: str
    target_signal_type: SignalType
    seals: tuple[TraceOutcomeSeal, ...]
    created_by: str
    created_at: datetime

    def __post_init__(self) -> None:
        _aware(self.created_at, "created_at")
        if not self.cohort_id or not self.created_by or not self.seals:
            raise ValueError("cohort identity, creator, and at least one seal are required")
        _digest(self.trace_cohort_hash)
        if any(seal.target_signal_type != self.target_signal_type for seal in self.seals):
            raise ValueError("all seals must use the cohort target signal type")
        project_ids = [seal.project_id for seal in self.seals]
        if len(project_ids) != len(set(project_ids)):
            raise ValueError("outcome cohort cannot contain duplicate project IDs")

    @property
    def observed_count(self) -> int:
        return sum(seal.outcome_state == TraceOutcomeState.OBSERVED for seal in self.seals)

    @property
    def not_observed_count(self) -> int:
        return sum(seal.outcome_state == TraceOutcomeState.NOT_OBSERVED_BY_CUTOFF for seal in self.seals)

    @property
    def inconclusive_count(self) -> int:
        return sum(seal.outcome_state == TraceOutcomeState.INCONCLUSIVE for seal in self.seals)

    @property
    def cohort_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "trailforge-retrospective-outcome-cohort-v1",
            "cohort_id": self.cohort_id,
            "trace_cohort_hash": self.trace_cohort_hash,
            "target_signal_type": self.target_signal_type,
            "seals": [seal.as_dict() for seal in self.seals],
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "observed_count": self.observed_count,
            "not_observed_count": self.not_observed_count,
            "inconclusive_count": self.inconclusive_count,
            "cohort_hash": self.cohort_hash,
        }


def build_outcome_cohort(paths: tuple[str, ...] | list[str], *, cohort_id: str,
                         trace_cohort_hash: str, target_signal_type: SignalType,
                         created_by: str, created_at: datetime) -> RetrospectiveOutcomeCohort:
    seals = tuple(load_outcome_seal(path) for path in paths)
    return RetrospectiveOutcomeCohort(cohort_id, trace_cohort_hash, target_signal_type,
                                      seals, created_by, created_at)


def write_outcome_cohort(cohort: RetrospectiveOutcomeCohort, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"outcome cohort output already exists: {destination}")
    destination.write_text(json.dumps(cohort.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
