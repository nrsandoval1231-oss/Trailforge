"""Reproducible run manifests and historical fixture boundaries."""
from __future__ import annotations

import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
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
        datetime.now(timezone.utc).isoformat(), source_commit, config or {},
        {"python": sys.version.split()[0], "platform": platform.platform()}, world.replay_hash())
    return manifest, observations


def manifest_dict(manifest: RunManifest) -> dict[str, Any]:
    return asdict(manifest) | {"manifest_hash": manifest.manifest_hash}
