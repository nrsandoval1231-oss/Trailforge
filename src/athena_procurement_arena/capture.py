"""Turn one manually reviewed public listing into a screenable fixture bundle.

Capture is the funnel, not a discovery feed.  It performs no network access and
invents no facts: every field comes from the operator, and the source digest is
computed from a saved excerpt of the listing text, so a record cannot exist
without the evidence it claims to rest on.

The emitted bundle is validated through the same fail-closed path as any
checked-in bundle, and the same intake screen decides the verdict; this module
adds no second qualification implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .fixtures import FixtureBundle, VerifiedFixture, content_fingerprint
from .foundation import EvidenceEvent, GroundTruth, Scenario
from .rfp_intake import screen_aura_rental_candidate

CANDIDATE_STATUS = "VERIFIED"
DEFAULT_OUTCOME = "SOLICITATION_RELEASED"


def _aware(value: str, label: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a UTC offset, e.g. 2026-09-14T09:00:00-05:00")
    return parsed


def _seed(scenario_id: str) -> int:
    """Derive a stable seed; `hash()` is salted per process and would not replay."""
    return int(content_fingerprint(scenario_id)[:8], 16)


def _tenant(buyer: str) -> str:
    slug = "".join(character if character.isalnum() else "-" for character in buyer.lower())
    return "public-" + "-".join(part for part in slug.split("-") if part)


@dataclass(frozen=True)
class CaptureRequest:
    """Operator-supplied facts for a single reviewed listing."""

    fixture_id: str
    source_url: str
    excerpt: str
    buyer: str
    scope: str
    published_at: str
    retrieved_at: str
    verified_by: str
    verification_notes: str
    lifecycle: str = "OPEN"
    required_kw: float | None = None
    fuel: str | None = None
    solicitation_number: str | None = None
    closes_at: str | None = None

    def __post_init__(self) -> None:
        required = {
            "fixture_id": self.fixture_id, "source_url": self.source_url, "excerpt": self.excerpt,
            "buyer": self.buyer, "scope": self.scope, "verified_by": self.verified_by,
            "verification_notes": self.verification_notes,
        }
        missing = sorted(name for name, value in required.items() if not str(value).strip())
        if missing:
            raise ValueError(f"missing required capture fields: {', '.join(missing)}")


def _claims(request: CaptureRequest) -> dict[str, Any]:
    """Build the claim mapping from captured facts only; absent stays absent."""
    claims: dict[str, Any] = {
        "solicitation": "released",
        "scope": request.scope,
        "buyer": request.buyer,
    }
    if request.solicitation_number:
        claims["solicitation_number"] = request.solicitation_number
    if request.required_kw is not None:
        claims["required_kw"] = request.required_kw
    if request.fuel:
        claims["required_fuel"] = request.fuel
    return claims


def build_candidate_bundle(request: CaptureRequest) -> FixtureBundle:
    """Return a validated single-fixture bundle for one reviewed listing."""
    published = _aware(request.published_at, "published_at")
    retrieved = _aware(request.retrieved_at, "retrieved_at")
    timeline = [published]
    if request.closes_at:
        closes = _aware(request.closes_at, "closes_at")
        if closes <= published:
            raise ValueError("closes_at must follow published_at")
        timeline.append(closes)

    scenario_id = request.fixture_id.lower()
    tenant = _tenant(request.buyer)
    evidence = EvidenceEvent(
        evidence_id=f"{request.fixture_id}-publication",
        source_id=request.source_url,
        event_date=published,
        document_date=published,
        verified_available_at=published,
        observed_at=retrieved,
        claims=_claims(request),
        claim_basis="OFFICIAL_SOURCE",
        source_version=f"capture-{retrieved.date().isoformat()}",
        lineage_family=scenario_id,
        tenant_id=tenant,
        authority="OFFICIAL_PROCUREMENT_SOURCE",
        source_spans=("captured excerpt",),
        entity_candidates=(request.buyer,),
        permission_scope="PUBLIC",
    )
    scenario = Scenario(
        scenario_id, "1", _seed(scenario_id), tuple(timeline), (evidence,),
        GroundTruth(request.fixture_id, DEFAULT_OUTCOME, published), tenant,
    )
    fixture = VerifiedFixture(
        request.fixture_id, CANDIDATE_STATUS, scenario, request.source_url,
        content_fingerprint(request.excerpt), request.retrieved_at, request.verified_by,
        request.verification_notes, request.lifecycle,
    )
    return FixtureBundle(scenario_id, "1", (fixture,))


def capture_listing(request: CaptureRequest, *, out_path: str | Path | None = None) -> dict[str, Any]:
    """Build, optionally persist, and immediately screen one captured listing."""
    bundle = build_candidate_bundle(request)
    fixture = bundle.fixtures[0]
    screen = screen_aura_rental_candidate(fixture.scenario.evidence)
    written = None
    if out_path is not None:
        destination = Path(out_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(bundle.dumps(), encoding="utf-8")
        written = str(destination)
    return {
        "status": "PASS",
        "mode": "capture",
        "bundle_id": bundle.bundle_id,
        "fixture_id": fixture.fixture_id,
        "source_url": fixture.source_url,
        "source_sha256": fixture.source_sha256,
        "opportunity_status": fixture.opportunity_status,
        "current": fixture.current,
        "shortlisted": fixture.current and screen.status.value == "QUALIFIED",
        "screen": screen.as_dict(),
        "written": written,
    }
