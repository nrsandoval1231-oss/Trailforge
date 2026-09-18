"""Deterministic project-signal chronology with separated evidence classes."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from athena_arena.contracts import canonical_hash


class EvidenceClass(StrEnum):
    PUBLIC = "PUBLIC"
    CONFIDENTIAL = "CONFIDENTIAL"


class SignalType(StrEnum):
    PROJECT_ANNOUNCED = "PROJECT_ANNOUNCED"
    FEASIBILITY_COMPLETE = "FEASIBILITY_COMPLETE"
    PERMIT_FILED = "PERMIT_FILED"
    PERMIT_APPROVED = "PERMIT_APPROVED"
    EPCM_AWARDED = "EPCM_AWARDED"
    CONSTRUCTION_APPROVED = "CONSTRUCTION_APPROVED"
    POWER_REQUIREMENT = "POWER_REQUIREMENT"
    FUEL_SELECTED = "FUEL_SELECTED"
    PROCUREMENT_SIGNAL = "PROCUREMENT_SIGNAL"
    CONSTRUCTION_STARTED = "CONSTRUCTION_STARTED"
    OPERATING = "OPERATING"


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _digest(value: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value.lower()):
        raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
    return value.lower()


@dataclass(frozen=True)
class ProjectSignal:
    signal_id: str
    project_id: str
    observed_at: datetime
    signal_type: SignalType
    title: str
    evidence_class: EvidenceClass
    source_sha256: str
    verified_by: str
    claims: dict[str, Any]
    source_url: str | None = None
    source_ref: str | None = None
    source_quote: str | None = None

    def __post_init__(self) -> None:
        _aware(self.observed_at, "observed_at")
        if not self.signal_id or not self.project_id or not self.title or not self.verified_by:
            raise ValueError("signal_id, project_id, title, and verified_by are required")
        _digest(self.source_sha256)
        if self.evidence_class == EvidenceClass.PUBLIC:
            if not self.source_url or not self.source_url.startswith(("https://", "http://")):
                raise ValueError("public evidence requires an HTTP(S) source_url")
        elif not self.source_ref:
            raise ValueError("confidential evidence requires a source_ref")
        object.__setattr__(self, "claims", dict(self.claims))

    @property
    def signal_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "trailforge-project-signal-v1",
            "signal_id": self.signal_id,
            "project_id": self.project_id,
            "observed_at": self.observed_at.isoformat(),
            "signal_type": self.signal_type,
            "title": self.title,
            "evidence_class": self.evidence_class,
            "source_url": self.source_url,
            "source_ref": self.source_ref,
            "source_quote": self.source_quote,
            "source_sha256": self.source_sha256,
            "verified_by": self.verified_by,
            "claims": self.claims,
            "signal_hash": self.signal_hash,
        }


@dataclass(frozen=True)
class ProjectTrace:
    project_id: str
    signals: tuple[ProjectSignal, ...]

    def __post_init__(self) -> None:
        if not self.project_id or not self.signals:
            raise ValueError("project_id and at least one signal are required")
        if any(item.project_id != self.project_id for item in self.signals):
            raise ValueError("all signals must belong to the trace project")
        ordered = tuple(sorted(self.signals, key=lambda item: (item.observed_at, item.signal_id)))
        if ordered != self.signals:
            object.__setattr__(self, "signals", ordered)

    @property
    def earliest_signal(self) -> ProjectSignal:
        return self.signals[0]

    @property
    def trace_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, Any]:
        return {"schema_version": "trailforge-project-trace-v1", "project_id": self.project_id,
                "signals": [item.as_dict() for item in self.signals], "trace_hash": self.trace_hash}


def trace_project_signals(signals: tuple[ProjectSignal, ...] | list[ProjectSignal]) -> tuple[ProjectTrace, ...]:
    """Group signals by exact project identity and sort each trace deterministically."""
    grouped: dict[str, list[ProjectSignal]] = {}
    for signal in signals:
        grouped.setdefault(signal.project_id, []).append(signal)
    return tuple(ProjectTrace(project_id, tuple(items)) for project_id, items in sorted(grouped.items()))


def write_trace(trace: ProjectTrace, path: str | Path) -> None:
    Path(path).write_text(json.dumps(trace.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def load_trace(path: str | Path) -> ProjectTrace:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema_version") != "trailforge-project-trace-v1":
        raise ValueError("unsupported project trace schema_version")
    signals = []
    for item in raw.get("signals", ()):
        signals.append(ProjectSignal(
            signal_id=item["signal_id"], project_id=item["project_id"],
            observed_at=datetime.fromisoformat(item["observed_at"]),
            signal_type=SignalType(item["signal_type"]), title=item["title"],
            evidence_class=EvidenceClass(item["evidence_class"]),
            source_url=item.get("source_url"), source_ref=item.get("source_ref"),
            source_quote=item.get("source_quote"),
            source_sha256=item["source_sha256"], verified_by=item["verified_by"],
            claims=item.get("claims", {}),
        ))
    trace = ProjectTrace(raw["project_id"], tuple(signals))
    if raw.get("trace_hash") != trace.trace_hash:
        raise ValueError("project trace hash mismatch")
    return trace
