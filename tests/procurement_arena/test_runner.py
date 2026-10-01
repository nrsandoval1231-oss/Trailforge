import json
from datetime import UTC, datetime

import pytest

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
    loaded = load_manifest(path)
    assert loaded == manifest
    assert verify_replay(loaded, scenario, BaselineA())["status"] == "PASS"


@pytest.mark.parametrize("mutation", ["missing", "malformed", "config", "source_commit"])
def test_load_manifest_rejects_missing_malformed_or_tampered_hash(tmp_path, mutation):
    t = datetime(2026, 1, 1, tzinfo=UTC)
    scenario = Scenario("manifest", "1", 8, (t,), (), GroundTruth("p", "OPEN"))
    manifest, _ = run_with_manifest(scenario, BaselineA.policy_id, BaselineA())
    payload = manifest_dict(manifest)
    if mutation == "missing":
        del payload["manifest_hash"]
    elif mutation == "malformed":
        payload["manifest_hash"] = "bad"
    elif mutation == "config":
        payload["config"]["changed"] = True
    else:
        payload["source_commit"] = "0" * 40
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest_hash"):
        load_manifest(path)


def test_verify_replay_fails_when_local_source_commit_differs(monkeypatch):
    t = datetime(2026, 1, 1, tzinfo=UTC)
    scenario = Scenario("manifest", "1", 8, (t,), (), GroundTruth("p", "OPEN"))
    manifest, _ = run_with_manifest(scenario, BaselineA.policy_id, BaselineA())

    class Result:
        stdout = "0" * 40

    monkeypatch.setattr("athena_procurement_arena.runner.subprocess.run", lambda *args, **kwargs: Result())
    report = verify_replay(manifest, scenario, BaselineA())
    assert report["status"] == "FAIL"
    assert report["checks"]["source_commit"] is False


def test_verify_replay_fails_closed_when_local_source_commit_is_unavailable(monkeypatch):
    import subprocess

    t = datetime(2026, 1, 1, tzinfo=UTC)
    scenario = Scenario("manifest", "1", 8, (t,), (), GroundTruth("p", "OPEN"))
    manifest, _ = run_with_manifest(scenario, BaselineA.policy_id, BaselineA())

    def unavailable(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])

    monkeypatch.setattr("athena_procurement_arena.runner.subprocess.run", unavailable)
    report = verify_replay(manifest, scenario, BaselineA())
    assert report["status"] == "FAIL"
    assert report["checks"]["source_commit"] is False


def test_verify_replay_fails_closed_when_git_returns_no_commit(monkeypatch):
    t = datetime(2026, 1, 1, tzinfo=UTC)
    scenario = Scenario("manifest", "1", 8, (t,), (), GroundTruth("p", "OPEN"))
    manifest, _ = run_with_manifest(scenario, BaselineA.policy_id, BaselineA())

    class Result:
        stdout = ""

    monkeypatch.setattr("athena_procurement_arena.runner.subprocess.run", lambda *args, **kwargs: Result())
    report = verify_replay(manifest, scenario, BaselineA())
    assert report["status"] == "FAIL"
    assert report["checks"]["source_commit"] is False
