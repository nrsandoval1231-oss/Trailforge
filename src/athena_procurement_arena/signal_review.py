"""Human-reviewed conversion of raw captures into project signals."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from athena_arena.contracts import canonical_hash

from .public_capture import PublicCapture
from .signal_ledger import ProjectSignal, SignalType


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True)
class SignalCandidate:
    candidate_id: str
    project_id: str
    observed_at: datetime
    signal_type: SignalType
    title: str
    source_url: str
    source_sha256: str
    capture_hash: str
    source_quote: str
    claims: dict[str, Any]
    proposed_by: str

    def __post_init__(self) -> None:
        _aware(self.observed_at, "observed_at")
        if not all((self.candidate_id, self.project_id, self.title, self.source_url,
                    self.source_sha256, self.capture_hash, self.source_quote, self.proposed_by)):
            raise ValueError("candidate identity, provenance, quote, and proposer are required")
        object.__setattr__(self, "claims", dict(self.claims))

    @property
    def candidate_hash(self) -> str:
        return canonical_hash(self)


def candidate_from_capture(capture: PublicCapture, *, candidate_id: str, project_id: str,
                           observed_at: datetime, signal_type: SignalType, title: str,
                           source_quote: str, claims: dict[str, Any], proposed_by: str) -> SignalCandidate:
    """Create a candidate only when the proposed quote exists in raw capture text."""
    if not source_quote or source_quote not in capture.content:
        raise ValueError("source_quote must be an exact span in the captured content")
    return SignalCandidate(
        candidate_id, project_id, observed_at, signal_type, title, capture.source_url,
        capture.content_sha256, capture.capture_hash, source_quote, claims, proposed_by,
    )


def accept_candidate(candidate: SignalCandidate, capture: PublicCapture, *, signal_id: str,
                     reviewed_by: str, reviewed_at: datetime | None = None) -> ProjectSignal:
    """Accept a candidate with an explicit reviewer and preserve its capture binding."""
    if candidate.capture_hash != capture.capture_hash or candidate.source_sha256 != capture.content_sha256:
        raise ValueError("candidate is not bound to the supplied capture")
    if candidate.source_quote not in capture.content:
        raise ValueError("candidate quote is absent from the supplied capture")
    reviewed_at = reviewed_at or datetime.now(UTC)
    _aware(reviewed_at, "reviewed_at")
    claims = dict(candidate.claims)
    claims["candidate_id"] = candidate.candidate_id
    claims["candidate_hash"] = candidate.candidate_hash
    claims["reviewed_at"] = reviewed_at.isoformat()
    return ProjectSignal(
        signal_id=signal_id, project_id=candidate.project_id, observed_at=candidate.observed_at,
        signal_type=candidate.signal_type, title=candidate.title, evidence_class="PUBLIC",
        source_sha256=candidate.source_sha256, verified_by=reviewed_by, claims=claims,
        source_url=candidate.source_url, source_quote=candidate.source_quote,
    )


def write_signal(signal: ProjectSignal, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"signal output already exists: {destination}")
    destination.write_text(json.dumps(signal.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
