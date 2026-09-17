import json
from types import SimpleNamespace

from athena_procurement_arena import cli
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


def test_cli_unit_executes_pytest_and_propagates_its_status(monkeypatch, capsys):
    monkeypatch.setattr(cli.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="2 passed"))
    assert main(["unit"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS" and payload["returncode"] == 0

    monkeypatch.setattr(cli.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="1 failed"))
    assert main(["unit"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "FAIL" and payload["returncode"] == 1
from datetime import UTC, datetime

from athena_procurement_arena import (
    BaselineA,
    capture_prospective_shadow,
    write_shadow_record,
)


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

