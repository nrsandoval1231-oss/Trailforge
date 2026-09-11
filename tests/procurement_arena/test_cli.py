import json

from athena_procurement_arena.campaign import synthetic_scenario
from athena_procurement_arena.cli import main
from athena_procurement_arena.scenario_dsl import ScenarioDsl


def test_cli_smoke_emits_machine_readable_manifest(capsys):
    assert main(["smoke", "--seed", "5"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS" and payload["policy_id"] == "BASELINE_A"

def test_cli_historical_is_explicitly_unverified(capsys):
    main(["historical"])
    payload = json.loads(capsys.readouterr().out)
    assert all(item["status"] == "UNVERIFIED" for item in payload["fixtures"])

def test_cli_adversarial_and_tournament_execute_governed_paths(capsys):
    main(["adversarial", "--seed", "5"])
    adversarial = json.loads(capsys.readouterr().out)
    main(["tournament"])
    tournament = json.loads(capsys.readouterr().out)
    assert adversarial["predicted_state"] == "UNKNOWN"
    assert tournament["governance"]["outcome"] == "QUARANTINE"


def test_cli_shortlist_emits_only_current_qualified_provenance(tmp_path, capsys):
    scenario = synthetic_scenario(5)
    scenario_raw = json.loads(ScenarioDsl.dumps(scenario))
    for evidence in scenario_raw["evidence"]:
        evidence["claims"] = {
            "scope": "TEMPORARY_POWER_OR_INSTALLATION",
            "temporary": "power_or_installation",
            "prime_power": "continuous",
            "required_kw": 300,
        }
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps({
        "schema_version": "procurement-arena-fixture-bundle-v1",
        "bundle_id": "cli-test",
        "version": "1",
        "fixtures": [{
            "fixture_id": "current-1",
            "status": "VERIFIED",
            "opportunity_status": "OPEN",
            "source_url": "https://example.com/current-1",
            "source_sha256": "a" * 64,
            "retrieved_at": "2026-09-08T12:00:00+00:00",
            "verified_by": "human-reviewer",
            "verification_notes": "Current source checked.",
            "scenario": scenario_raw,
        }],
    }), encoding="utf-8")

    assert main(["shortlist", "--bundle", str(bundle_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 1
    assert payload["fixtures"][0]["source_url"] == "https://example.com/current-1"


def test_cli_validate_bundle_reports_holdout_gate(tmp_path, capsys):
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps({
        "schema_version": "procurement-arena-fixture-bundle-v1",
        "bundle_id": "validation-test", "version": "1", "fixtures": [],
        "holdout_fixture_ids": [],
    }), encoding="utf-8")
    assert main(["validate-bundle", "--bundle", str(bundle_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"bundle_id": "validation-test", "fixtures": 0,
                       "holdout_available": False, "mode": "validate-bundle", "status": "PASS"}
