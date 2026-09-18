"""Reviewer-controlled identity joins for project signal traces."""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from athena_arena.contracts import canonical_hash

from .signal_ledger import EvidenceClass, ProjectTrace


def _digest(value: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value.lower()):
        raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
    return value.lower()


@dataclass(frozen=True)
class ProjectIdentityReview:
    """An explicit, evidence-bound assertion that project IDs refer to one project."""

    review_id: str
    canonical_project_id: str
    member_project_ids: tuple[str, ...]
    evidence_class: EvidenceClass
    source_sha256: str
    source_quote: str
    reviewed_by: str
    reviewed_at: datetime
    rationale: str
    source_url: str | None = None
    source_ref: str | None = None

    def __post_init__(self) -> None:
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise ValueError("reviewed_at must be timezone-aware")
        if not self.review_id or not self.canonical_project_id or not self.reviewed_by:
            raise ValueError("review_id, canonical_project_id, and reviewed_by are required")
        members = tuple(dict.fromkeys(self.member_project_ids))
        if not members or any(not item for item in members):
            raise ValueError("at least one non-empty member_project_id is required")
        if self.canonical_project_id not in members:
            members = (self.canonical_project_id, *members)
        object.__setattr__(self, "member_project_ids", members)
        if not self.source_quote or not self.rationale:
            raise ValueError("source_quote and rationale are required")
        _digest(self.source_sha256)
        if self.evidence_class == EvidenceClass.PUBLIC:
            if not self.source_url or not self.source_url.startswith(("https://", "http://")):
                raise ValueError("public identity evidence requires an HTTP(S) source_url")
        elif not self.source_ref:
            raise ValueError("confidential identity evidence requires a source_ref")

    @property
    def review_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "trailforge-project-identity-review-v1",
            "review_id": self.review_id,
            "canonical_project_id": self.canonical_project_id,
            "member_project_ids": list(self.member_project_ids),
            "evidence_class": self.evidence_class,
            "source_sha256": self.source_sha256,
            "source_url": self.source_url,
            "source_ref": self.source_ref,
            "source_quote": self.source_quote,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat(),
            "rationale": self.rationale,
            "review_hash": self.review_hash,
        }


def load_identity_reviews(path: str | Path) -> tuple[ProjectIdentityReview, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    items = raw.get("reviews", raw if isinstance(raw, list) else ())
    reviews = []
    for item in items:
        review = ProjectIdentityReview(
            review_id=item["review_id"], canonical_project_id=item["canonical_project_id"],
            member_project_ids=tuple(item["member_project_ids"]),
            evidence_class=EvidenceClass(item["evidence_class"]), source_sha256=item["source_sha256"],
            source_url=item.get("source_url"), source_ref=item.get("source_ref"),
            source_quote=item["source_quote"], reviewed_by=item["reviewed_by"],
            reviewed_at=datetime.fromisoformat(item["reviewed_at"]), rationale=item["rationale"],
        )
        if item.get("review_hash") != review.review_hash:
            raise ValueError("identity review hash mismatch")
        reviews.append(review)
    return tuple(reviews)


def resolve_traces(traces: tuple[ProjectTrace, ...] | list[ProjectTrace],
                   reviews: tuple[ProjectIdentityReview, ...] | list[ProjectIdentityReview]) -> tuple[ProjectTrace, ...]:
    """Apply only explicit, non-conflicting identity joins and preserve review provenance."""
    mapping: dict[str, ProjectIdentityReview] = {}
    for review in reviews:
        for member in review.member_project_ids:
            existing = mapping.get(member)
            if existing and existing.canonical_project_id != review.canonical_project_id:
                raise ValueError(f"conflicting identity reviews for project id: {member}")
            mapping[member] = review
    grouped: dict[str, list] = {}
    for trace in traces:
        review = mapping.get(trace.project_id)
        canonical_id = review.canonical_project_id if review else trace.project_id
        for signal in trace.signals:
            if review:
                claims = {**signal.claims, "identity_review_id": review.review_id,
                          "identity_review_hash": review.review_hash}
                signal = replace(signal, project_id=canonical_id, claims=claims)
            grouped.setdefault(canonical_id, []).append(signal)
    return tuple(ProjectTrace(project_id, tuple(sorted(signals, key=lambda item: (item.observed_at, item.signal_id))))
                 for project_id, signals in sorted(grouped.items()))


def write_resolved_traces(traces: tuple[ProjectTrace, ...] | list[ProjectTrace], path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"resolved trace output already exists: {destination}")
    payload = {"schema_version": "trailforge-resolved-traces-v1",
               "traces": [trace.as_dict() for trace in traces]}
    destination.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
