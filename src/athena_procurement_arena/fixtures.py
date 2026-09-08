"""Fail-closed source provenance and sealed-holdout fixture bundles."""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .scenario_dsl import ScenarioDsl

ALLOWED_STATUSES = frozenset({"VERIFIED", "SEALED_READY"})
OPPORTUNITY_STATUSES = frozenset({"OPEN", "ACTIVE", "SOURCES_SOUGHT", "CLOSED", "AWARDED", "INACTIVE", "UNKNOWN"})
CURRENT_OPPORTUNITY_STATUSES = frozenset({"OPEN", "ACTIVE", "SOURCES_SOUGHT"})


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("fixture timestamps must include a timezone")
    return parsed


def _sha256(value: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value.lower()):
        raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
    return value.lower()


@dataclass(frozen=True)
class VerifiedFixture:
    fixture_id: str
    status: str
    scenario: Any
    source_url: str
    source_sha256: str
    retrieved_at: str
    verified_by: str
    verification_notes: str
    opportunity_status: str = "UNKNOWN"

    def __post_init__(self) -> None:
        if not self.fixture_id:
            raise ValueError("fixture_id is required")
        if self.status not in ALLOWED_STATUSES:
            raise ValueError("fixture status must be VERIFIED or SEALED_READY")
        if not self.source_url.startswith(("https://", "http://")):
            raise ValueError("source_url must be an http(s) URL")
        _sha256(self.source_sha256)
        _timestamp(self.retrieved_at)
        if not self.verified_by or not self.verification_notes:
            raise ValueError("verified_by and verification_notes are required")
        if self.opportunity_status not in OPPORTUNITY_STATUSES:
            raise ValueError("invalid opportunity_status")

    @property
    def scoreable(self) -> bool:
        return self.status == "SEALED_READY"

    @property
    def current(self) -> bool:
        return self.opportunity_status in CURRENT_OPPORTUNITY_STATUSES

    def as_dict(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "status": self.status,
            "source_url": self.source_url,
            "source_sha256": self.source_sha256,
            "retrieved_at": self.retrieved_at,
            "verified_by": self.verified_by,
            "verification_notes": self.verification_notes,
            "opportunity_status": self.opportunity_status,
            "scenario": json.loads(ScenarioDsl.dumps(self.scenario)),
        }


@dataclass(frozen=True)
class FixtureBundle:
    bundle_id: str
    version: str
    fixtures: tuple[VerifiedFixture, ...]
    holdout_fixture_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ids = tuple(item.fixture_id for item in self.fixtures)
        if not self.bundle_id or self.version != "1":
            raise ValueError("bundle_id and version 1 are required")
        if len(set(ids)) != len(ids):
            raise ValueError("fixture IDs must be unique")
        if not set(self.holdout_fixture_ids).issubset(ids):
            raise ValueError("holdout IDs must refer to fixtures in the bundle")
        if any(not next(item for item in self.fixtures if item.fixture_id == fixture_id).scoreable
               for fixture_id in self.holdout_fixture_ids):
            raise ValueError("holdout fixtures must be SEALED_READY")

    @property
    def sealed_holdout_available(self) -> bool:
        return bool(self.holdout_fixture_ids) and all(
            item.scoreable for item in self.fixtures if item.fixture_id in self.holdout_fixture_ids
        )

    def as_dict(self) -> dict[str, Any]:
        return {"schema_version": "procurement-arena-fixture-bundle-v1", "bundle_id": self.bundle_id,
                "version": self.version, "holdout_fixture_ids": list(self.holdout_fixture_ids),
                "fixtures": [item.as_dict() for item in self.fixtures]}

    def dumps(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))


def load_bundle_mapping(raw: dict[str, Any]) -> FixtureBundle:
    if raw.get("schema_version") != "procurement-arena-fixture-bundle-v1":
        raise ValueError("unsupported fixture bundle schema_version")
    fixtures = []
    for item in raw.get("fixtures", ()):
        fixtures.append(VerifiedFixture(
            item["fixture_id"], item["status"], ScenarioDsl.from_mapping(item["scenario"]),
            item["source_url"], item["source_sha256"], item["retrieved_at"],
            item["verified_by"], item["verification_notes"], item.get("opportunity_status", "UNKNOWN"),
        ))
    return FixtureBundle(raw["bundle_id"], str(raw["version"]), tuple(fixtures),
                         tuple(raw.get("holdout_fixture_ids", ())))


def load_bundle(path: str | Path) -> FixtureBundle:
    return load_bundle_mapping(json.loads(Path(path).read_text(encoding="utf-8")))


def split_fixture_ids(fixture_ids: tuple[str, ...], *, holdout_ratio: float = 0.2,
                      seed: int = 1) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split IDs deterministically; this marks allocation, not verification."""
    if not fixture_ids or not 0 < holdout_ratio < 1:
        raise ValueError("fixture IDs and a holdout ratio between 0 and 1 are required")
    if len(set(fixture_ids)) != len(fixture_ids):
        raise ValueError("fixture IDs must be unique")
    shuffled = list(fixture_ids)
    random.Random(seed).shuffle(shuffled)
    count = max(1, round(len(shuffled) * holdout_ratio)) if len(shuffled) > 1 else 0
    holdout = tuple(sorted(shuffled[:count]))
    train = tuple(sorted(shuffled[count:]))
    return train, holdout


def content_fingerprint(text: str) -> str:
    """Return the canonical digest callers can compare with source_sha256."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def score_fixture_bundle(policy_id: str, policy: Any, bundle: FixtureBundle, *, subset: str = "holdout") -> dict[str, Any]:
    """Score exact final procurement states; holdout scoring requires SEALED_READY."""
    if subset not in {"train", "holdout"}:
        raise ValueError("subset must be train or holdout")
    if subset == "holdout":
        if not bundle.sealed_holdout_available:
            raise ValueError("sealed holdout is unavailable")
        selected = tuple(item for item in bundle.fixtures if item.fixture_id in bundle.holdout_fixture_ids)
    else:
        selected = tuple(item for item in bundle.fixtures if item.fixture_id not in bundle.holdout_fixture_ids)
    if not selected:
        raise ValueError(f"no fixtures available for {subset} scoring")
    from .world import TemporalWorld
    correct = 0
    invariant_failures = 0
    predictions = []
    for item in selected:
        world = TemporalWorld(item.scenario, policy_id, policy)
        world.run()
        invariant_failures += int(not world.ledger.verify())
        predicted = world.ledger.records[-1].forecast.get("procurement", {}).get("state", "UNKNOWN")
        outcome = item.scenario.truth.outcome
        correct += int(predicted == outcome)
        predictions.append({"fixture_id": item.fixture_id, "predicted": predicted, "actual": outcome,
                            "correct": predicted == outcome})
    return {"status": "PASS", "subset": subset, "scoreable": subset == "holdout",
            "fixtures": len(selected), "correct": correct,
            "accuracy": round(correct / len(selected), 6),
            "invariant_failures": invariant_failures, "predictions": predictions}


def current_target_fixtures(bundle: FixtureBundle) -> tuple[VerifiedFixture, ...]:
    """Return current, source-verified fixtures meeting the 300 kW prime target."""
    from .policies import classify_target

    return tuple(
        item for item in bundle.fixtures
        if item.current
        and classify_target(item.scenario.evidence) == "IN_SCOPE_PRIME_POWER_300KW_PLUS"
    )
