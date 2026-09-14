"""The review queue: discovered rows awaiting a human decision.

A `ReviewCandidate` is explicitly *not* evidence.  It carries no verifier, no
verification notes, and no VERIFIED status, and it cannot reach the shortlist.
Converting one into a real record requires `candidate_to_capture_request`, which
demands a named reviewer and the retrieved source text -- the same bar a
hand-authored fixture has always had.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..capture import CaptureRequest
from .triage import TriageScore, triage_score


@dataclass(frozen=True)
class ReviewCandidate:
    """One discovered listing, ranked and awaiting human review."""

    source_id: str
    title: str
    url: str
    retrieved_at: str
    buyer: str = ""
    published: str = ""
    closes: str = ""
    solicitation_number: str = ""
    summary: str = ""
    jurisdiction: str = ""
    cache_path: str | None = None
    raw: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if not (self.title or self.summary):
            raise ValueError("a candidate needs at least a title or summary")

    @property
    def triage(self) -> TriageScore:
        return triage_score(" ".join(
            part for part in (self.title, self.summary, self.buyer, self.solicitation_number) if part))

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id, "jurisdiction": self.jurisdiction,
            "title": self.title, "url": self.url, "buyer": self.buyer,
            "published": self.published, "closes": self.closes,
            "solicitation_number": self.solicitation_number, "summary": self.summary,
            "retrieved_at": self.retrieved_at, "cache_path": self.cache_path,
            "triage": self.triage.as_dict(),
            "status": "AWAITING_REVIEW",
        }


def candidate_to_capture_request(
    candidate: ReviewCandidate, *, verified_by: str, verification_notes: str,
    excerpt: str, fixture_id: str, scope: str | None = None,
    published_at: str | None = None, lifecycle: str = "OPEN",
    required_kw: float | None = None, fuel: str | None = None,
) -> CaptureRequest:
    """Promote a reviewed candidate into a capture request.

    The reviewer must supply their identity, what the source does and does not
    establish, and the retrieved source text.  Capacity and fuel stay optional and
    unfilled unless the reviewer read them in the source, so an unreviewed field
    reaches the screen as missing evidence rather than as a qualification.
    """
    if not verified_by.strip() or not verification_notes.strip():
        raise ValueError("promoting a candidate requires verified_by and verification_notes")
    resolved_published = published_at or candidate.published
    if not resolved_published:
        raise ValueError(
            "published_at is required; the listing did not expose a parsable publication date")
    return CaptureRequest(
        fixture_id=fixture_id,
        source_url=candidate.url,
        excerpt=excerpt,
        buyer=candidate.buyer or candidate.source_id,
        scope=scope or candidate.title or candidate.summary,
        published_at=resolved_published,
        retrieved_at=candidate.retrieved_at,
        verified_by=verified_by,
        verification_notes=verification_notes,
        lifecycle=lifecycle,
        required_kw=required_kw,
        fuel=fuel,
        solicitation_number=candidate.solicitation_number or None,
        closes_at=candidate.closes or None,
    )
