"""Local immutable prospective outcome sealing, cohort evaluation, and governance floors."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from athena_arena.contracts import canonical_hash

from .shadow import ProspectiveShadowRecord, _require_aware, _validate_digest
from .tournament import meets_floors, pareto_dominates


@dataclass(frozen=True)
class ProspectiveOutcomeSeal:
    """A shadow prediction bound to a later-verified outcome, with no authority."""

    seal_id: str
    shadow_record: ProspectiveShadowRecord
    verified_outcome: str
    verified_at: datetime
    verified_by: str
    evaluation: dict[str, Any]
    execution_authority: str = "ABSENT"

    def __post_init__(self) -> None:
        if not self.seal_id:
            raise ValueError("seal_id is required")
        if not self.verified_outcome:
            raise ValueError("verified_outcome is required")
        _require_aware(self.verified_at, "verified_at")
        if not self.verified_by:
            raise ValueError("verified_by is required")
        if self.execution_authority != "ABSENT":
            raise ValueError("prospective outcome seal has no execution authority")
        if "predicted" not in self.evaluation or "actual" not in self.evaluation:
            raise ValueError("evaluation must contain predicted and actual outcomes")

    @property
    def seal_hash(self) -> str:
        return canonical_hash(self)


def evaluate_prediction(predicted: str, actual: str) -> dict[str, Any]:
    """Return deterministic exact-match evaluation."""
    return {"predicted": predicted, "actual": actual, "correct": predicted == actual}


def seal_prospective_outcome(
    shadow_record: ProspectiveShadowRecord,
    *,
    seal_id: str,
    verified_outcome: str,
    verified_at: datetime,
    verified_by: str,
) -> ProspectiveOutcomeSeal:
    """Bind a captured shadow prediction to a verified final outcome."""
    predicted = shadow_record.manifest.get("metrics", {}).get("final_procurement_state", "UNKNOWN")
    evaluation = evaluate_prediction(predicted, verified_outcome)
    return ProspectiveOutcomeSeal(
        seal_id=seal_id,
        shadow_record=shadow_record,
        verified_outcome=verified_outcome,
        verified_at=verified_at,
        verified_by=verified_by,
        evaluation=evaluation,
    )


@dataclass(frozen=True)
class ProspectiveCohort:
    """An aggregate of sealed outcomes with metrics and a governance floor check."""

    cohort_id: str
    seals: tuple[ProspectiveOutcomeSeal, ...]
    metrics: dict[str, Any]
    governance: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.cohort_id:
            raise ValueError("cohort_id is required")
        ids = tuple(seal.seal_id for seal in self.seals)
        if len(set(ids)) != len(ids):
            raise ValueError("seal IDs must be unique within a cohort")


def evaluate_cohort(
    cohort_id: str,
    seals: tuple[ProspectiveOutcomeSeal, ...],
    *,
    floors: dict[str, float] | None = None,
    incumbent_metrics: dict[str, float] | None = None,
) -> ProspectiveCohort:
    """Aggregate sealed outcomes and apply governance floors."""
    if not seals:
        raise ValueError("cohort requires at least one seal")
    correct = sum(1 for seal in seals if seal.evaluation.get("correct"))
    total = len(seals)
    incorrect = total - correct
    metrics = {
        "seals": total,
        "correct": correct,
        "incorrect": incorrect,
        "accuracy": round(correct / total, 6),
    }
    floors = floors or {"accuracy": 0.0}
    incumbent = incumbent_metrics or {"accuracy": 0.0}
    governance = {
        "meets_floors": meets_floors(metrics, floors),
        "pareto_dominates": pareto_dominates(metrics, incumbent, minimize=("incorrect",)),
        "floor": dict(floors),
        "incumbent": dict(incumbent),
    }
    return ProspectiveCohort(cohort_id, seals, metrics, governance)


def _shadow_as_dict(shadow: ProspectiveShadowRecord) -> dict[str, Any]:
    return {
        "record_id": shadow.record_id,
        "captured_at": shadow.captured_at.isoformat(),
        "source_url": shadow.source_url,
        "source_sha256": shadow.source_sha256,
        "verified_by": shadow.verified_by,
        "manifest": shadow.manifest,
        "prediction_hash": shadow.prediction_hash,
        "execution_authority": shadow.execution_authority,
        "record_hash": shadow.record_hash,
    }


def _shadow_from_dict(raw: dict[str, Any]) -> ProspectiveShadowRecord:
    return ProspectiveShadowRecord(
        record_id=raw["record_id"],
        captured_at=datetime.fromisoformat(raw["captured_at"]),
        source_url=raw["source_url"],
        source_sha256=_validate_digest(raw["source_sha256"]),
        verified_by=raw["verified_by"],
        manifest=dict(raw["manifest"]),
        prediction_hash=raw["prediction_hash"],
        execution_authority=raw["execution_authority"],
    )


def seal_as_dict(seal: ProspectiveOutcomeSeal) -> dict[str, Any]:
    return {
        "schema_version": "procurement-arena-prospective-outcome-seal-v1",
        "seal_id": seal.seal_id,
        "shadow_record": _shadow_as_dict(seal.shadow_record),
        "verified_outcome": seal.verified_outcome,
        "verified_at": seal.verified_at.isoformat(),
        "verified_by": seal.verified_by,
        "evaluation": seal.evaluation,
        "execution_authority": seal.execution_authority,
        "seal_hash": seal.seal_hash,
    }


def seal_from_dict(raw: dict[str, Any]) -> ProspectiveOutcomeSeal:
    if raw.get("schema_version") != "procurement-arena-prospective-outcome-seal-v1":
        raise ValueError("unsupported prospective outcome seal schema_version")
    return ProspectiveOutcomeSeal(
        seal_id=raw["seal_id"],
        shadow_record=_shadow_from_dict(raw["shadow_record"]),
        verified_outcome=raw["verified_outcome"],
        verified_at=datetime.fromisoformat(raw["verified_at"]),
        verified_by=raw["verified_by"],
        evaluation=dict(raw["evaluation"]),
    )


def cohort_as_dict(cohort: ProspectiveCohort) -> dict[str, Any]:
    return {
        "schema_version": "procurement-arena-prospective-cohort-v1",
        "cohort_id": cohort.cohort_id,
        "seals": [seal_as_dict(seal) for seal in cohort.seals],
        "metrics": cohort.metrics,
        "governance": cohort.governance,
    }


def cohort_from_dict(raw: dict[str, Any]) -> ProspectiveCohort:
    if raw.get("schema_version") != "procurement-arena-prospective-cohort-v1":
        raise ValueError("unsupported prospective cohort schema_version")
    return ProspectiveCohort(
        cohort_id=raw["cohort_id"],
        seals=tuple(seal_from_dict(item) for item in raw["seals"]),
        metrics=dict(raw["metrics"]),
        governance=dict(raw["governance"]),
    )


def write_seal(seal: ProspectiveOutcomeSeal, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(seal_as_dict(seal), sort_keys=True, indent=2), encoding="utf-8")
    return target


def load_seal(path: str | Path) -> ProspectiveOutcomeSeal:
    return seal_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def write_cohort(cohort: ProspectiveCohort, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(cohort_as_dict(cohort), sort_keys=True, indent=2), encoding="utf-8")
    return target


def load_cohort(path: str | Path) -> ProspectiveCohort:
    return cohort_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
