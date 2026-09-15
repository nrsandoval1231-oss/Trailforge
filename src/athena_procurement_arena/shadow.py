"""Immutable, local capture records for a prospective shadow cohort."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from athena_arena.contracts import canonical_hash

from .foundation import Scenario
from .runner import manifest_dict, run_with_manifest


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _validate_digest(value: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value.lower()):
        raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
    return value.lower()


@dataclass(frozen=True)
class ProspectiveShadowRecord:
    """A prediction capture that intentionally contains no outcome or authority."""

    record_id: str
    captured_at: datetime
    source_url: str
    source_sha256: str
    verified_by: str
    manifest: dict[str, Any]
    prediction_hash: str
    execution_authority: str = "ABSENT"

    def __post_init__(self) -> None:
        if not self.record_id or not self.source_url.startswith(("https://", "http://")):
            raise ValueError("record_id and an http(s) source_url are required")
        _require_aware(self.captured_at, "captured_at")
        _validate_digest(self.source_sha256)
        if not self.verified_by:
            raise ValueError("verified_by is required")
        if self.execution_authority != "ABSENT":
            raise ValueError("prospective shadow capture has no execution authority")
        if "outcome" in self.manifest or "verified_outcome" in self.manifest:
            raise ValueError("prospective shadow capture cannot contain an outcome")

    @property
    def record_hash(self) -> str:
        return canonical_hash(self)


def capture_prospective_shadow(*, record_id: str, captured_at: datetime, source_url: str,
                               source_sha256: str, verified_by: str, scenario: Scenario,
                               policy_id: str, policy: Any, known_outcome: Any = None) -> ProspectiveShadowRecord:
    """Freeze a local prediction from manually captured, point-in-time evidence only."""
    if known_outcome is not None:
        raise ValueError("prospective shadow capture cannot accept a known outcome")
    _require_aware(captured_at, "captured_at")
    manifest, _ = run_with_manifest(
        scenario,
        policy_id,
        policy,
        experiment_id=record_id,
        mode="prospective_shadow",
        config={"execution_authority": "ABSENT"},
        created_at=captured_at,
    )
    payload = manifest_dict(manifest)
    return ProspectiveShadowRecord(
        record_id,
        captured_at,
        source_url,
        _validate_digest(source_sha256),
        verified_by,
        payload,
        manifest.result_hash,
    )
