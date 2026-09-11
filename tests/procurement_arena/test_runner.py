from datetime import UTC, datetime

from athena_procurement_arena import BaselineA, GroundTruth, Scenario
from athena_procurement_arena.runner import (
    historical_registry,
    historical_replay,
    load_manifest,
    manifest_dict,
    run_with_manifest,
    verify_replay,
    write_manifest,
)


def test_historical_registry_is_unverified_until_availability_is_verified():
    registry = historical_registry()
    assert tuple(item["fixture_id"] for item in registry) == tuple(f"GT-00{i}" for i in range(1, 7))
    assert all(item["status"] == "UNVERIFIED" and item["scoreable"] == "false" for item in registry)
    assert historical_replay("GT-001")["scoreable"] is False
    assert historical_replay("GT-001", status="SEALED_READY")["scoreable"] is True

def test_manifest_contains_replay_hash_and_stable_manifest_hash_shape(tmp_path):
    t = datetime(2026, 1, 1, tzinfo=UTC)
    scenario = Scenario("manifest", "1", 8, (t,), (), GroundTruth("p", "OPEN"))
    manifest, observations = run_with_manifest(scenario, BaselineA.policy_id, BaselineA())
    payload = manifest_dict(manifest)
    assert observations and payload["result_hash"] and len(payload["manifest_hash"]) == 64
    assert len(payload["source_commit"]) == 40
    assert payload["invariant_results"]["ledger"] is True and "decision_count" in payload["metrics"]
    assert verify_replay(manifest, scenario, BaselineA())["status"] == "PASS"
    path = write_manifest(manifest, tmp_path / "manifest.json")
    assert verify_replay(load_manifest(path), scenario, BaselineA())["status"] == "PASS"
