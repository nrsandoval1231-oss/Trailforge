import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from athena_procurement_arena import BaselineA, capture_prospective_shadow, cli, write_shadow_record
from athena_procurement_arena.campaign import synthetic_scenario
from athena_procurement_arena.cli import main
from athena_procurement_arena.scenario_dsl import ScenarioDsl


def test_cli_smoke_emits_machine_readable_manifest(capsys):
    assert main(["smoke", "--seed", "5"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS" and payload["policy_id"] == "BASELINE_A"


def test_cli_scenario_manifest_replays_in_separate_process(tmp_path):
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(ScenarioDsl.dumps(synthetic_scenario(5)), encoding="utf-8")
    manifest_path = tmp_path / "nested" / "manifest.json"
    module = [sys.executable, "-m", "athena_procurement_arena"]
    run = subprocess.run(module + ["scenario", "--scenario-file", str(scenario_path), "--output", str(manifest_path)],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["invariant_results"]["ledger"] is True
    replay = subprocess.run(module + ["replay", "--scenario-file", str(scenario_path), "--manifest", str(manifest_path)],
                            capture_output=True, text=True)
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert json.loads(replay.stdout)["checks"] == {
        "scenario_hash": True, "result_hash": True, "source_commit": True}
    original = manifest_path.read_bytes()
    overwrite = subprocess.run(module + ["scenario", "--scenario-file", str(scenario_path), "--output", str(manifest_path)],
                               capture_output=True, text=True)
    assert overwrite.returncode != 0
    assert manifest_path.read_bytes() == original


def test_cli_durable_experiment_save_inspect_replay_and_no_overwrite(tmp_path, capsys):
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(ScenarioDsl.dumps(synthetic_scenario(5)), encoding="utf-8")
    experiment = tmp_path / "saved-experiment"
    assert main(["scenario", "--scenario-file", str(scenario_path), "--experiment-dir", str(experiment)]) == 0
    capsys.readouterr()
    assert main(["inspect", "--experiment-dir", str(experiment)]) == 0
    rendered = capsys.readouterr().out
    assert re.search(r'\n  "decisions": \{', rendered)
    inspected = json.loads(rendered)
    assert inspected["evaluation"]["status"] == "UNSEALED"
    assert main(["replay", "--experiment-dir", str(experiment)]) == 0
    assert json.loads(capsys.readouterr().out)["checks"]["result_hash"] is True
    before = {item.name: item.read_bytes() for item in experiment.iterdir()}
    assert main(["scenario", "--scenario-file", str(scenario_path), "--experiment-dir", str(experiment)]) == 1
    capsys.readouterr()
    assert before == {item.name: item.read_bytes() for item in experiment.iterdir()}


def test_cli_scenario_and_replay_fail_closed_on_inputs(tmp_path, capsys):
    assert main(["scenario"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "FAIL"


@pytest.mark.parametrize("manifest_json", ["null", '"manifest"', "42", "[]"])
def test_cli_replay_non_object_manifest_fails_machine_readably(tmp_path, capsys, manifest_json):
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(ScenarioDsl.dumps(synthetic_scenario(5)), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(manifest_json, encoding="utf-8")

    assert main(["replay", "--scenario-file", str(scenario_path), "--manifest", str(manifest_path)]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "FAIL"
    assert payload["mode"] == "replay"
    assert payload["error"]
    bad_scenario = tmp_path / "bad.json"
    bad_scenario.write_text("{", encoding="utf-8")
    assert main(["scenario", "--scenario-file", str(bad_scenario), "--output", str(tmp_path / "m.json")]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "FAIL"
    assert main(["replay", "--scenario-file", str(bad_scenario), "--manifest", str(tmp_path / "missing.json")]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "FAIL"


def test_cli_scenario_rejects_existing_manifest_without_changing_it(tmp_path, capsys):
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(ScenarioDsl.dumps(synthetic_scenario(5)), encoding="utf-8")
    output_path = tmp_path / "manifest.json"
    output_path.write_bytes(b"preserve-me")
    assert main(["scenario", "--scenario-file", str(scenario_path), "--output", str(output_path)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "FAIL"
    assert output_path.read_bytes() == b"preserve-me"

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

def test_cli_campaign_propagates_invariant_failure(monkeypatch, capsys):
    monkeypatch.setattr(cli, "run_campaign", lambda *args, **kwargs: {
        "status": "FAIL", "policies": {"BASELINE_A": {"invariant_failures": 1}}})
    assert main(["batch", "--count", "1"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "FAIL"

def test_cli_adversarial_propagates_bad_ledger(monkeypatch, capsys):
    import athena_procurement_arena.world as world_module
    class BadLedger:
        records = (SimpleNamespace(forecast={"procurement": {"state": "UNKNOWN"}}),)

        def verify(self):
            return False

    class BadWorld:
        def __init__(self, *args, **kwargs):
            self.ledger = BadLedger()

        def run(self):
            return ()

    monkeypatch.setattr(world_module, "TemporalWorld", BadWorld)
    assert main(["adversarial", "--seed", "5"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "FAIL" and payload["invariant_failures"] == 1


def test_cli_shortlist_emits_only_current_qualified_provenance(tmp_path, capsys):
    scenario = synthetic_scenario(5)
    scenario_raw = json.loads(ScenarioDsl.dumps(scenario))
    for evidence in scenario_raw["evidence"]:
        evidence["claims"] = {
            "scope": "TEMPORARY_POWER_OR_INSTALLATION",
            "temporary": "power_or_installation",
            "commissioning_scope": "planned temporary power",
            "required_kw": 300,
            "primary_fuel": "natural gas",
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
    assert payload["fixtures"][0]["screen"]["status"] == "QUALIFIED"


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


def test_cli_screen_bundle_explains_every_fixture_and_next_action(tmp_path, capsys):
    scenario = synthetic_scenario(5)
    scenario_raw = json.loads(ScenarioDsl.dumps(scenario))
    for evidence in scenario_raw["evidence"]:
        evidence["claims"] = {"construction_scope": "planned bridge power", "program_mw": 400}
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps({
        "schema_version": "procurement-arena-fixture-bundle-v1",
        "bundle_id": "screen-test", "version": "1",
        "fixtures": [{
            "fixture_id": "held-1", "status": "VERIFIED", "opportunity_status": "OPEN",
            "source_url": "https://example.com/held-1", "source_sha256": "a" * 64,
            "retrieved_at": "2026-09-08T12:00:00+00:00", "verified_by": "reviewer",
            "verification_notes": "Requirement needs verification.", "scenario": scenario_raw,
        }, {
            "fixture_id": "closed-1", "status": "VERIFIED", "opportunity_status": "CLOSED",
            "source_url": "https://example.com/closed-1", "source_sha256": "b" * 64,
            "retrieved_at": "2026-09-08T12:00:00+00:00", "verified_by": "reviewer",
            "verification_notes": "Closed record.", "scenario": scenario_raw,
        }],
    }), encoding="utf-8")

    assert main(["screen-bundle", "--bundle", str(bundle_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 2
    assert payload["counts"] == {"NEEDS_REVIEW": 1, "NOT_CURRENT": 1, "QUALIFIED": 0, "REJECTED": 0}
    by_id = {item["fixture_id"]: item for item in payload["fixtures"]}
    assert by_id["held-1"]["next_action"] == "VERIFY_PER_PROJECT_REQUIRED_CAPACITY"
    assert by_id["closed-1"]["disposition"] == "NOT_CURRENT"
    assert by_id["closed-1"]["next_action"] == "ARCHIVE_OR_MONITOR_LIFECYCLE"


def test_cli_unit_executes_pytest_and_propagates_its_status(monkeypatch, capsys):
    monkeypatch.setattr(cli.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="2 passed"))
    assert main(["unit"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS" and payload["returncode"] == 0

    monkeypatch.setattr(cli.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="1 failed"))
    assert main(["unit"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "FAIL" and payload["returncode"] == 1
def test_cli_seal_prospective_creates_outcome_seal(tmp_path, capsys):
    shadow = capture_prospective_shadow(
        record_id="cli-shadow-1",
        captured_at=datetime(2026, 9, 14, tzinfo=UTC),
        source_url="https://example.com/record",
        source_sha256="a" * 64,
        verified_by="human-reviewer",
        scenario=synthetic_scenario(8),
        policy_id="BASELINE_A",
        policy=BaselineA(),
    )
    shadow_path = tmp_path / "shadow.json"
    write_shadow_record(shadow, shadow_path)
    predicted = shadow.manifest["metrics"]["final_procurement_state"]
    seal_path = tmp_path / "seal.json"
    assert main([
        "seal-prospective",
        "--shadow", str(shadow_path),
        "--outcome", predicted,
        "--verified-by", "outcome-reviewer",
        "--output", str(seal_path),
    ]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS"
    assert payload["mode"] == "seal-prospective"
    assert seal_path.exists()


def test_cli_evaluate_cohort_aggregates_seals(tmp_path, capsys):
    seal_paths = []
    expected_correct = 0
    for i in range(3):
        seed = 8 + i
        record = capture_prospective_shadow(
            record_id=f"cli-shadow-{i}",
            captured_at=datetime(2026, 9, 14, tzinfo=UTC),
            source_url="https://example.com/record",
            source_sha256="a" * 64,
            verified_by="human-reviewer",
            scenario=synthetic_scenario(seed),
            policy_id="BASELINE_A",
            policy=BaselineA(),
        )
        predicted = record.manifest["metrics"]["final_procurement_state"]
        # Two correct, one deliberately wrong
        outcome = predicted if i < 2 else ("AWARDED" if predicted != "AWARDED" else "SOLICITATION_RELEASED")
        expected_correct += int(outcome == predicted)
        shadow_path = tmp_path / f"shadow-{i}.json"
        write_shadow_record(record, shadow_path)
        seal_path = tmp_path / f"seal-{i}.json"
        main([
            "seal-prospective",
            "--shadow", str(shadow_path),
            "--outcome", outcome,
            "--verified-by", "outcome-reviewer",
            "--output", str(seal_path),
        ])
        seal_paths.append(str(seal_path))

    cohort_path = tmp_path / "cohort.json"
    capsys.readouterr()  # flush prior seal-prospective output
    assert main([
        "evaluate-cohort",
        "--seals", *seal_paths,
        "--cohort-id", "cli-cohort-1",
        "--floor-accuracy", "0.5",
        "--incumbent-accuracy", "0.5",
        "--output", str(cohort_path),
    ]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS"
    assert payload["mode"] == "evaluate-cohort"
    assert payload["metrics"]["seals"] == 3
    assert payload["metrics"]["correct"] == expected_correct
    assert cohort_path.exists()

