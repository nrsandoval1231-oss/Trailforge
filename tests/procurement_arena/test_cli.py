import json
from athena_procurement_arena.cli import main

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
    assert tournament["outcome"] == "QUARANTINE"
