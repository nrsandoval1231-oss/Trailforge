"""Deterministic local manifests for pending RFP candidate review."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from athena_arena.contracts import canonical_hash

from .rfp_candidate_capture import load_rfp_candidate

PENDING_REVIEW = "PENDING_REVIEW"


@dataclass(frozen=True, slots=True)
class RfpCandidateQueueRecord:
    """Allowlisted immutable reference to one pending candidate."""

    path: str
    candidate_id: str
    candidate_hash: str
    review_status: str = PENDING_REVIEW

    def validate(self) -> None:
        if not self.path.strip() or not self.candidate_id.strip():
            raise ValueError("queue record path and candidate_id are required")
        if len(self.candidate_hash) != 64 or any(
            character not in "0123456789abcdef" for character in self.candidate_hash.lower()
        ):
            raise ValueError("queue record candidate_hash must be a 64-character hexadecimal digest")
        if self.review_status != PENDING_REVIEW:
            raise ValueError("every queue record must remain PENDING_REVIEW")

    def as_dict(self) -> dict[str, str]:
        self.validate()
        return {
            "path": self.path,
            "candidate_id": self.candidate_id,
            "candidate_hash": self.candidate_hash.lower(),
            "review_status": self.review_status,
        }


@dataclass(frozen=True)
class RfpCandidateQueue:
    """Hash-bound references to candidates awaiting human review."""

    queue_id: str
    assembled_by: str
    assembled_at: datetime
    records: tuple[RfpCandidateQueueRecord, ...]

    def __post_init__(self) -> None:
        if not self.queue_id.strip() or not self.assembled_by.strip() or not self.records:
            raise ValueError("queue_id, assembled_by, and at least one candidate are required")
        if self.assembled_at.tzinfo is None or self.assembled_at.utcoffset() is None:
            raise ValueError("assembled_at must be timezone-aware")
        self._validate_records()
        candidate_ids = [record.candidate_id for record in self.records]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("queue cannot contain duplicate candidate IDs")

    def _validate_records(self) -> None:
        for record in self.records:
            if not isinstance(record, RfpCandidateQueueRecord):
                raise ValueError("queue records must be immutable allowlisted records")
            record.validate()

    @property
    def candidate_count(self) -> int:
        return len(self.records)

    @property
    def queue_hash(self) -> str:
        return canonical_hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        self._validate_records()
        return {
            "schema_version": "trailforge-rfp-candidate-review-queue-v1",
            "queue_id": self.queue_id,
            "assembled_by": self.assembled_by,
            "assembled_at": self.assembled_at.isoformat(),
            "candidate_count": self.candidate_count,
            "records": [record.as_dict() for record in self.records],
        }

    def as_dict(self) -> dict[str, Any]:
        return self._hash_payload() | {"queue_hash": self.queue_hash}


def build_rfp_candidate_queue(
    paths: tuple[str, ...] | list[str], *, queue_id: str, assembled_by: str, assembled_at: datetime
) -> RfpCandidateQueue:
    """Load hash-valid candidates and bind their identities into a review queue."""
    if not paths:
        raise ValueError("at least one candidate path is required")
    candidates = tuple(load_rfp_candidate(path) for path in paths)
    records = tuple(
        RfpCandidateQueueRecord(
            path=str(path), candidate_id=candidate.candidate_id,
            candidate_hash=candidate.candidate_hash,
        )
        for path, candidate in zip(paths, candidates, strict=True)
    )
    return RfpCandidateQueue(queue_id, assembled_by, assembled_at, records)


def write_rfp_candidate_queue(queue: RfpCandidateQueue, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing RFP review queue: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(queue.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
