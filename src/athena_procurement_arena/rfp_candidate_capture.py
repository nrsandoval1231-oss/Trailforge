"""Hash-bound local RFP candidates with an explicit review boundary.

This module only handles excerpts already saved by an operator. It never
fetches a source, infers a requirement, or makes a commercial recommendation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from athena_arena.contracts import canonical_hash

from .fixtures import OPPORTUNITY_STATUSES, FixtureBundle, VerifiedFixture, content_fingerprint
from .foundation import ClaimBasis, EvidenceEvent, GroundTruth, Scenario

_ACCEPTABLE_STATUSES = OPPORTUNITY_STATUSES - {"UNKNOWN"}


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _source_hash(value: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value.lower()):
        raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
    return value.lower()


@dataclass(frozen=True)
class RfpCandidateCapture:
    """A proposed RFP record, deliberately separate from a verified fixture."""

    candidate_id: str
    source_url: str
    source_sha256: str
    source_quote: str
    buyer: str
    scope: str
    published_at: datetime
    retrieved_at: datetime
    captured_by: str
    required_kw: float | None = None
    fuel: str | None = None
    solicitation_number: str | None = None
    closes_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.buyer or not self.scope or not self.captured_by:
            raise ValueError("candidate_id, buyer, scope, and captured_by are required")
        if not self.source_url.startswith(("https://", "http://")):
            raise ValueError("source_url must be an http(s) URL")
        object.__setattr__(self, "source_sha256", _source_hash(self.source_sha256))
        if not self.source_quote.strip():
            raise ValueError("source_quote is required")
        _aware(self.published_at, "published_at")
        _aware(self.retrieved_at, "retrieved_at")
        if self.retrieved_at < self.published_at:
            raise ValueError("retrieved_at cannot precede published_at")
        if self.required_kw is not None and self.required_kw < 0:
            raise ValueError("required_kw cannot be negative")
        if self.closes_at is not None:
            _aware(self.closes_at, "closes_at")
            if self.closes_at < self.published_at:
                raise ValueError("closes_at cannot precede published_at")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "trailforge-rfp-candidate-capture-v1",
            "candidate_id": self.candidate_id,
            "source_url": self.source_url,
            "source_sha256": self.source_sha256,
            "source_quote": self.source_quote,
            "buyer": self.buyer,
            "scope": self.scope,
            "published_at": self.published_at.isoformat(),
            "retrieved_at": self.retrieved_at.isoformat(),
            "captured_by": self.captured_by,
            "required_kw": self.required_kw,
            "fuel": self.fuel,
            "solicitation_number": self.solicitation_number,
            "closes_at": self.closes_at.isoformat() if self.closes_at else None,
        }

    @property
    def candidate_hash(self) -> str:
        return canonical_hash(self.as_dict())


def candidate_from_excerpt(*, excerpt: str, candidate_id: str, source_url: str, buyer: str,
                           scope: str, published_at: datetime, retrieved_at: datetime,
                           captured_by: str, source_quote: str, required_kw: float | None = None,
                           fuel: str | None = None, solicitation_number: str | None = None,
                           closes_at: datetime | None = None) -> RfpCandidateCapture:
    """Create a candidate only when its review quote is literally in the excerpt."""
    if source_quote not in excerpt:
        raise ValueError("source_quote must be an exact span from the local excerpt")
    return RfpCandidateCapture(
        candidate_id=candidate_id, source_url=source_url, source_sha256=content_fingerprint(excerpt),
        source_quote=source_quote, buyer=buyer, scope=scope, published_at=published_at,
        retrieved_at=retrieved_at, captured_by=captured_by, required_kw=required_kw, fuel=fuel,
        solicitation_number=solicitation_number, closes_at=closes_at,
    )


def load_rfp_candidate(path: str | Path) -> RfpCandidateCapture:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema_version") != "trailforge-rfp-candidate-capture-v1":
        raise ValueError("unsupported RFP candidate schema_version")
    expected_hash = raw.pop("candidate_hash", None)
    candidate = RfpCandidateCapture(
        candidate_id=raw["candidate_id"], source_url=raw["source_url"], source_sha256=raw["source_sha256"],
        source_quote=raw["source_quote"], buyer=raw["buyer"], scope=raw["scope"],
        published_at=datetime.fromisoformat(raw["published_at"]), retrieved_at=datetime.fromisoformat(raw["retrieved_at"]),
        captured_by=raw["captured_by"], required_kw=raw.get("required_kw"), fuel=raw.get("fuel"),
        solicitation_number=raw.get("solicitation_number"),
        closes_at=datetime.fromisoformat(raw["closes_at"]) if raw.get("closes_at") else None,
    )
    if expected_hash != candidate.candidate_hash:
        raise ValueError("RFP candidate hash does not match its content")
    return candidate


def write_rfp_candidate(candidate: RfpCandidateCapture, path: str | Path) -> None:
    target = Path(path)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing candidate: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = candidate.as_dict() | {"candidate_hash": candidate.candidate_hash}
    target.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def accept_rfp_candidate(candidate: RfpCandidateCapture, *, excerpt: str, fixture_id: str,
                         reviewed_by: str, verification_notes: str,
                         opportunity_status: str) -> FixtureBundle:
    """Turn a candidate into a standard fixture after explicit human verification."""
    if not fixture_id or not reviewed_by.strip() or not verification_notes.strip():
        raise ValueError("fixture_id, reviewed_by, and verification_notes are required")
    if opportunity_status not in _ACCEPTABLE_STATUSES:
        raise ValueError("opportunity_status must be explicit and cannot be UNKNOWN")
    if content_fingerprint(excerpt) != candidate.source_sha256:
        raise ValueError("local excerpt hash does not match the candidate source hash")
    if candidate.source_quote not in excerpt:
        raise ValueError("candidate source_quote is absent from the local excerpt")

    claims: dict[str, Any] = {
        "solicitation": "released", "buyer": candidate.buyer, "scope": candidate.scope,
        "rfp_candidate_id": candidate.candidate_id, "rfp_candidate_hash": candidate.candidate_hash,
    }
    if candidate.required_kw is not None:
        claims["required_kw"] = candidate.required_kw
    if candidate.fuel:
        claims["required_fuel"] = candidate.fuel
    if candidate.solicitation_number:
        claims["solicitation_number"] = candidate.solicitation_number
    if candidate.closes_at:
        claims["closes_at"] = candidate.closes_at.isoformat()
    evidence = EvidenceEvent(
        evidence_id=f"rfp-candidate-{candidate.candidate_id}", source_id=candidate.source_url,
        event_date=candidate.published_at, document_date=candidate.published_at,
        verified_available_at=candidate.retrieved_at, observed_at=candidate.retrieved_at,
        claims=claims, claim_basis=ClaimBasis.REPORTED, source_version=candidate.candidate_hash,
        lineage_family=f"rfp-candidate:{candidate.candidate_id}", authority="REVIEWED_MANUAL_SOURCE",
        source_spans=(candidate.source_quote,), entity_candidates=(candidate.buyer,), permission_scope="PUBLIC",
    )
    timeline = tuple(sorted({candidate.published_at, candidate.retrieved_at, candidate.closes_at} - {None}))
    scenario = Scenario(
        scenario_id=fixture_id, version="1", seed=int(content_fingerprint(fixture_id)[:8], 16),
        timeline=timeline, evidence=(evidence,),
        truth=GroundTruth(fixture_id, "SOLICITATION_RELEASED", candidate.published_at),
    )
    fixture = VerifiedFixture(
        fixture_id=fixture_id, status="VERIFIED", scenario=scenario, source_url=candidate.source_url,
        source_sha256=candidate.source_sha256, retrieved_at=candidate.retrieved_at.isoformat(),
        verified_by=reviewed_by, verification_notes=verification_notes,
        opportunity_status=opportunity_status,
    )
    return FixtureBundle(bundle_id=f"candidate-{candidate.candidate_id}", version="1", fixtures=(fixture,))


def write_accepted_rfp_bundle(bundle: FixtureBundle, path: str | Path) -> None:
    target = Path(path)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing fixture bundle: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(bundle.dumps(), encoding="utf-8")
