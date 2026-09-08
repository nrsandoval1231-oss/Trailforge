from datetime import datetime, timezone
from athena_procurement_arena import BaselineA, GroundTruth, Scenario
from athena_procurement_arena.runner import historical_registry, historical_replay, manifest_dict, run_with_manifest, verify_replay

def test_historical_registry_is_unverified_until_availability_is_verified():
    registry = historical_registry()
    assert len(registry) == 6 and all(item["scoreable"] == "false" for item in registry)
    assert historical_replay("GT-001")["scoreable"] is False
    assert historical_replay("GT-001", status="SEALED_READY")["scoreable"] is True

def test_manifest_contains_replay_hash_and_stable_manifest_hash_shape():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    scenario = Scenario("manifest", "1", 8, (t,), (), GroundTruth("p", "OPEN"))
    manifest, observations = run_with_manifest(scenario, BaselineA.policy_id, BaselineA())
    payload = manifest_dict(manifest)
    assert observations and payload["result_hash"] and len(payload["manifest_hash"]) == 64
    assert len(payload["source_commit"]) == 40
    assert payload["invariant_results"]["ledger"] is True and "decision_count" in payload["metrics"]
    assert verify_replay(manifest, scenario, BaselineA())["status"] == "PASS"
