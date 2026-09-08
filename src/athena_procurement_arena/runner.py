"""Reproducible run manifests and historical fixture boundaries."""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from athena_arena.contracts import canonical_hash

from .foundation import Scenario
from .world import TemporalWorld


@dataclass(frozen=True)
class RunManifest:
    experiment_id: str
    mode: str
    scenario_hash: str
    policy_id: str
    seed: int
    created_at: str
    source_commit: str
    config: dict[str, Any]
    environment: dict[str, str]
    result_hash: str = ""
    metrics: dict[str, Any] = None
    invariant_results: dict[str, Any] = None
    artifact_paths: tuple[str, ...] = ()

    @property
    def manifest_hash(self) -> str:
        return canonical_hash(self)


HISTORICAL_FIXTURES = {
    "GT-001": "Waterleaf Great Salt Lake Phase 1",
    "GT-002": "Dallas County Youth Village",
    "GT-003": "Morgan Hill Generator Services",
    "GT-004": "Naperville Generator Replacement",
    "GT-005": "Puget Sound Naval Shipyard Generator Rentals",
    "GT-006": "San Bernardino National Forest Generator Rental/Rebid",
}


def historical_registry() -> tuple[dict[str, str], ...]:
    return tuple({"fixture_id": key, "name": name, "status": "UNVERIFIED", "scoreable": "false"}
                 for key, name in HISTORICAL_FIXTURES.items())


def historical_replay(fixture_id: str, *, status: str = "UNVERIFIED") -> dict[str, Any]:
    """Return a replay gate; current discoverability never implies historical availability."""
    if fixture_id not in HISTORICAL_FIXTURES:
        raise KeyError(f"unknown historical fixture: {fixture_id}")
    if status != "SEALED_READY":
        return {"fixture_id": fixture_id, "status": status, "scoreable": False,
                "reason": "timeline and verified availability are not sealed"}
    return {"fixture_id": fixture_id, "status": "SEALED_READY", "scoreable": True}


def run_with_manifest(scenario: Scenario, policy_id: str, policy: Any, *, experiment_id: str = "run-001",
                      mode: str = "scenario", config: dict[str, Any] | None = None) -> tuple[RunManifest, tuple[Any, ...]]:
    world = TemporalWorld(scenario, policy_id, policy)
    observations = world.run()
    try:
        source_commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                                      check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - only non-git copies
        source_commit = "UNCOMMITTED_LOCAL"
    manifest = RunManifest(experiment_id, mode, world.scenario_hash, policy_id, scenario.seed,
        datetime.now(UTC).isoformat(), source_commit, config or {},
        {"python": sys.version.split()[0], "platform": platform.platform()}, world.replay_hash(),
        {"decision_count": len(world.ledger.records)}, {"ledger": world.ledger.verify()}, ())
    return manifest, observations


def manifest_dict(manifest: RunManifest) -> dict[str, Any]:
    return asdict(manifest) | {"manifest_hash": manifest.manifest_hash}


def verify_replay(manifest: RunManifest, scenario: Scenario, policy: Any) -> dict[str, Any]:
    """Verify an existing manifest against a fresh deterministic replay."""
    world = TemporalWorld(scenario, manifest.policy_id, policy)
    world.run()
    checks = {"scenario_hash": world.scenario_hash == manifest.scenario_hash,
              "result_hash": world.replay_hash() == manifest.result_hash}
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "manifest_hash": manifest.manifest_hash}


def write_manifest(manifest: RunManifest, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest_dict(manifest), sort_keys=True, indent=2), encoding="utf-8")
    return target


def load_manifest(path: str | Path) -> RunManifest:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    raw.pop("manifest_hash", None)
    return RunManifest(**raw)
