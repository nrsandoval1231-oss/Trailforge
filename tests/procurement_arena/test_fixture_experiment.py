import hashlib
import json
from pathlib import Path

import pytest

from athena_procurement_arena.cli import main
from athena_procurement_arena.policies import BaselineA
from athena_procurement_arena.runner import verify_experiment


def _gt003_bundle_text():
    return (Path(__file__).parents[2] / "scenarios" / "fixtures" / "verified" /
            "gt-003-morgan-hill.json").read_text(encoding="utf-8")


def _rewrite_bound_input(directory, change):
    path = directory / "input.json"
    value = json.loads(path.read_text())
    change(value)
    data = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    path.write_bytes(data)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifacts"]["input.json"] = hashlib.sha256(data).hexdigest()
    from athena_arena.contracts import canonical_hash
    manifest["manifest_hash"] = canonical_hash(
        {key: item for key, item in manifest.items() if key != "manifest_hash"})
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")


def test_bundle_context_survives_source_unavailable_and_inspection_never_executes(tmp_path, monkeypatch, capsys):
    source = tmp_path / "bundle.json"
    original = _gt003_bundle_text()
    source.write_text(original, encoding="utf-8")
    experiment = tmp_path / "experiment"
    assert main(["scenario", "--bundle", str(source), "--fixture-id", "GT-003",
                 "--experiment-dir", str(experiment)]) == 0
    capsys.readouterr()
    source.unlink()
    import athena_procurement_arena.runner as runner
    monkeypatch.setattr(runner, "TemporalWorld", lambda *a, **k: (_ for _ in ()).throw(AssertionError("world ran")))
    monkeypatch.setattr(BaselineA, "__call__", lambda *a, **k: (_ for _ in ()).throw(AssertionError("policy ran")))
    assert main(["inspect", "--experiment-dir", str(experiment)]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["input"]["fixture_context"]["fixture_id"] == "GT-003"
    assert inspected["input"]["fixture_context"]["bundle_text"] == original
    assert inspected["evaluation"]["scoring"] == "UNSCORED"
    assert inspected["evaluation"]["status"] == "UNSEALED"


def test_bundle_source_unavailable_restart_replay_and_determinism(tmp_path, capsys):
    source = tmp_path / "bundle.json"
    bundle_text = _gt003_bundle_text()
    source.write_text(bundle_text, encoding="utf-8")
    first, second = tmp_path / "first", tmp_path / "second"
    assert main(["scenario", "--bundle", str(source), "--fixture-id", "GT-003", "--experiment-dir", str(first)]) == 0
    assert main(["scenario", "--bundle", str(source), "--fixture-id", "GT-003", "--experiment-dir", str(second)]) == 0
    source.unlink()
    _, first_files = verify_experiment(first)
    _, second_files = verify_experiment(second)
    assert first_files["input.json"]["fixture_context"]["bundle_sha256"] == hashlib.sha256(bundle_text.encode()).hexdigest()
    assert first_files["decisions.json"]["records"] == second_files["decisions.json"]["records"]
    assert first_files["input.json"]["fixture_context"]["fixture_id"] == "GT-003"
    assert main(["replay", "--experiment-dir", str(first)]) == 0


@pytest.mark.parametrize("fixture_id", ["missing", "GT-003"])
def test_bundle_rejects_unknown_id_mixed_flags_and_malformed_inputs(tmp_path, capsys, fixture_id):
    source = tmp_path / "bundle.json"
    source.write_text(_gt003_bundle_text(), encoding="utf-8")
    target = tmp_path / "missing-selection"
    args = ["scenario", "--bundle", str(source), "--fixture-id", fixture_id, "--experiment-dir", str(target)]
    if fixture_id == "GT-003":
        args.extend(["--scenario-file", str(source)])
    assert main(args) == 1
    assert not target.exists()
    source.write_text("{}", encoding="utf-8")
    assert main(["scenario", "--bundle", str(source), "--fixture-id", "GT-003",
                 "--experiment-dir", str(target)]) == 1
    assert not target.exists()
    source.write_text("not json", encoding="utf-8")
    assert main(["scenario", "--bundle", str(source), "--fixture-id", "GT-003",
                 "--experiment-dir", str(target)]) == 1
    assert not target.exists()


def test_context_tampering_and_rebound_wrong_scenario_fail_without_mutation(tmp_path):
    source = tmp_path / "bundle.json"
    source.write_text(_gt003_bundle_text(), encoding="utf-8")
    output = tmp_path / "experiment"
    assert main(["scenario", "--bundle", str(source), "--fixture-id", "GT-003", "--experiment-dir", str(output)]) == 0
    path = output / "input.json"
    value = json.loads(path.read_text())
    value["fixture_context"]["bundle_text"] += " "
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    before = {item.name: item.read_bytes() for item in output.iterdir()}
    with pytest.raises(ValueError, match="artifact hash"):
        verify_experiment(output)
    assert {item.name: item.read_bytes() for item in output.iterdir()} == before

    output2 = tmp_path / "rebound"
    assert main(["scenario", "--bundle", str(source), "--fixture-id", "GT-003", "--experiment-dir", str(output2)]) == 0
    def change_selected_fixture(saved):
        context = saved["fixture_context"]
        bundle = json.loads(context["bundle_text"])
        bundle["fixtures"][0]["scenario"]["seed"] += 1
        changed_text = json.dumps(bundle)
        context.update(bundle_text=changed_text,
                       bundle_sha256=hashlib.sha256(changed_text.encode()).hexdigest())

    _rewrite_bound_input(output2, change_selected_fixture)
    before = {item.name: item.read_bytes() for item in output2.iterdir()}
    with pytest.raises(ValueError, match="selected fixture scenario does not match retained input"):
        verify_experiment(output2)
    assert {item.name: item.read_bytes() for item in output2.iterdir()} == before


def test_saved_replay_rejects_source_selection_flags(tmp_path):
    source = tmp_path / "bundle.json"
    source.write_text(_gt003_bundle_text(), encoding="utf-8")
    output = tmp_path / "experiment"
    assert main(["scenario", "--bundle", str(source), "--fixture-id", "GT-003", "--experiment-dir", str(output)]) == 0
    assert main(["replay", "--bundle", str(source), "--fixture-id", "GT-003", "--experiment-dir", str(output)]) == 1


@pytest.mark.parametrize("inspection_mode", ["inspect", "replay"])
def test_explicit_null_fixture_context_fails_after_coherent_outer_rehash(tmp_path, capsys, inspection_mode):
    source = tmp_path / "bundle.json"
    source.write_text(_gt003_bundle_text(), encoding="utf-8")
    output = tmp_path / "experiment"
    assert main(["scenario", "--bundle", str(source), "--fixture-id", "GT-003", "--experiment-dir", str(output)]) == 0
    capsys.readouterr()
    _rewrite_bound_input(output, lambda saved: saved.update(fixture_context=None))
    before = {item.name: item.read_bytes() for item in output.iterdir()}
    assert main([inspection_mode, "--experiment-dir", str(output)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "FAIL"
    assert "fixture context is malformed" in result["error"]
    assert {item.name: item.read_bytes() for item in output.iterdir()} == before


@pytest.mark.parametrize("field", ["source_url", "scenario"])
@pytest.mark.parametrize("mode", ["initial", "retained"])
def test_malformed_nested_bundle_returns_structured_failure(tmp_path, capsys, field, mode):
    bundle = json.loads(_gt003_bundle_text())
    bundle["fixtures"][0][field] = None
    source = tmp_path / "bundle.json"
    source.write_text(json.dumps(bundle), encoding="utf-8")
    output = tmp_path / "experiment"
    if mode == "initial":
        assert main(["scenario", "--bundle", str(source), "--fixture-id", "GT-003", "--experiment-dir", str(output)]) == 1
        assert not output.exists()
        result = json.loads(capsys.readouterr().out)
        assert result["status"] == "FAIL"
        assert "error" in result
        return
    valid_source = tmp_path / "valid.json"
    valid_source.write_text(_gt003_bundle_text(), encoding="utf-8")
    assert main(["scenario", "--bundle", str(valid_source), "--fixture-id", "GT-003", "--experiment-dir", str(output)]) == 0
    capsys.readouterr()
    changed_text = json.dumps(bundle)
    _rewrite_bound_input(output, lambda saved: saved["fixture_context"].update(
        bundle_text=changed_text, bundle_sha256=hashlib.sha256(changed_text.encode()).hexdigest()))
    before = {item.name: item.read_bytes() for item in output.iterdir()}
    for operation in ("inspect", "replay"):
        assert main([operation, "--experiment-dir", str(output)]) == 1
        result = json.loads(capsys.readouterr().out)
        assert result["status"] == "FAIL"
        assert "malformed" in result["error"]
        assert {item.name: item.read_bytes() for item in output.iterdir()} == before
    assert output.joinpath("manifest.json").exists()


@pytest.mark.parametrize("mode", ["scenario", "replay"])
@pytest.mark.parametrize("flag", ["--bundle", "--fixture-id"])
def test_legacy_scenario_and_replay_reject_fixture_flags_without_output(tmp_path, capsys, mode, flag):
    source = tmp_path / "scenario.json"
    source.write_text(json.dumps({"schema_version": "procurement-arena-scenario-v1", "scenario_id": "s",
        "version": "1", "seed": 1, "tenant_id": "t", "timeline": [], "evidence": [],
        "truth": {"procurement_episode_id": "p", "outcome": "OPEN"}}), encoding="utf-8")
    output = tmp_path / "legacy.json"
    args = [mode, "--scenario-file", str(source)]
    args.extend([flag, str(source) if flag == "--bundle" else "GT-003"])
    args.extend(["--output", str(output)] if mode == "scenario" else ["--manifest", str(output)])
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2
    assert not output.exists()
