import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from athena_procurement_arena import runner
from athena_procurement_arena.cli import main
from athena_procurement_arena.foundation import ActionSupportAttestation
from athena_procurement_arena.policies import BaselineA
from athena_procurement_arena.runner import create_experiment, replay_experiment, verify_experiment
from athena_procurement_arena.scenario_dsl import ScenarioDsl
from athena_procurement_arena.world import TemporalWorld


def _scenario_text():
    return json.dumps({
        "schema_version": "procurement-arena-scenario-v1", "scenario_id": "durable",
        "version": "1", "seed": 4, "tenant_id": "default",
        "timeline": ["2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00"],
        "evidence": [
            {"evidence_id": "early", "source_id": "s1", "event_date": "2026-01-01T00:00:00+00:00",
             "document_date": "2026-01-01T00:00:00+00:00", "verified_available_at": "2026-01-01T00:00:00+00:00",
             "observed_at": "2026-01-01T00:00:00+00:00", "claims": {"title": "generator installation"}},
            {"evidence_id": "late", "source_id": "s2", "event_date": "2026-01-01T00:00:00+00:00",
             "document_date": "2026-01-01T00:00:00+00:00", "verified_available_at": "2026-01-02T00:00:00+00:00",
             "observed_at": "2026-01-02T00:00:00+00:00", "claims": {"later": "outcome detail"}},
        ],
        "truth": {"procurement_episode_id": "p", "outcome": "OPEN"},
    })


def test_persisted_experiment_contains_input_ordered_snapshots_and_unsealed_eval(tmp_path):
    source = _scenario_text()
    output = tmp_path / "experiment"
    create_experiment(source, "original/case.json", output, BaselineA())
    manifest, files = verify_experiment(output)
    assert set(p.name for p in output.iterdir()) == {
        "input.json", "decisions.json", "evaluation.json", "config.json", "manifest.json"
    }
    assert files["input.json"]["input_sha256"] == hashlib.sha256(source.encode()).hexdigest()
    snapshots = files["decisions.json"]["decision_snapshots"]
    assert [item["decision_time"] for item in snapshots] == [
        "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00"
    ]
    assert "late" not in snapshots[0]["policy_input"]["visible_evidence_ids"]
    assert files["evaluation.json"]["status"] == "UNSEALED"
    assert files["evaluation.json"]["scoring"] == "UNSCORED"
    assert files["evaluation.json"]["declared_truth"]["values"]["outcome"] == "OPEN"
    assert files["evaluation.json"]["later_evidence"]["values"][-1]["evidence_id"] == "late"
    assert "late" not in json.dumps(snapshots[0])
    assert manifest["artifacts"].keys() == {"input.json", "decisions.json", "evaluation.json", "config.json"}
    assert replay_experiment(output, BaselineA())["status"] == "PASS"


@pytest.mark.parametrize("filename", ["input.json", "decisions.json", "evaluation.json", "config.json"])
def test_tampering_required_artifact_fails_without_repair(tmp_path, filename):
    output = tmp_path / "experiment"
    create_experiment(_scenario_text(), "case.json", output, BaselineA())
    path = output / filename
    original = path.read_bytes()
    path.write_bytes(original + b" ")
    tampered = path.read_bytes()
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_experiment(output)
    assert path.read_bytes() == tampered


def test_missing_hash_entry_and_missing_file_are_rejected(tmp_path):
    output = tmp_path / "experiment"
    create_experiment(_scenario_text(), "case.json", output, BaselineA())
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    del manifest["artifacts"]["config.json"]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="artifact set"):
        verify_experiment(output)

    second = tmp_path / "second"
    create_experiment(_scenario_text(), "case.json", second, BaselineA())
    (second / "config.json").unlink()
    with pytest.raises(ValueError, match="missing or unsafe"):
        verify_experiment(second)


def test_world_snapshot_is_detached_and_future_review_hidden():
    scenario = ScenarioDsl.loads(_scenario_text())
    policy_inputs = []

    def mutating_policy(state):
        policy_inputs.append(state)
        forecast = {"procurement": {"state": "UNKNOWN"}, "evidence": list(state["visible_evidence_ids"])}
        frozen_forecast = forecast
        frozen_forecast["procurement"]["state"] = "AWARDED"
        return frozen_forecast, "RESEARCH"

    world = TemporalWorld(scenario, "BASELINE_A", mutating_policy)
    world.run()
    snapshots = world.decision_snapshots
    assert "late" not in snapshots[0]["policy_input"]["visible_evidence_ids"]
    assert "late" in snapshots[1]["policy_input"]["visible_evidence_ids"]
    policy_inputs[0]["visible_evidence_ids"] = ("forged",)
    assert snapshots[0]["policy_input"]["visible_evidence_ids"] == ("early",)
    assert snapshots[0]["policy_output"]["procurement"]["state"] == "AWARDED"

    reviewed = ScenarioDsl.loads(_scenario_text())
    event = reviewed.evidence[1]
    object.__setattr__(event, "action_support", ActionSupportAttestation(
        "p", "PREPARE", "reviewer", reviewed.timeline[1], "span", "reviewed later"))
    reviewed_world = TemporalWorld(reviewed, "BASELINE_A", BaselineA())
    reviewed_world.run()
    earlier = reviewed_world.decision_snapshots[0]["policy_input"]
    later = reviewed_world.decision_snapshots[1]["policy_input"]
    assert earlier["visible_evidence"][0]["action_support"] is None
    assert later["visible_evidence"][1]["action_support"]["reviewer"] == "reviewer"


def _rewrite_bound_artifact(directory, filename, change):
    path = directory / filename
    value = json.loads(path.read_text())
    change(value)
    data = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    path.write_bytes(data)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifacts"][filename] = hashlib.sha256(data).hexdigest()
    from athena_arena.contracts import canonical_hash
    manifest["manifest_hash"] = canonical_hash({key: item for key, item in manifest.items() if key != "manifest_hash"})
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")


def _rewrite_decisions_with_consistent_ledger(directory, change):
    from athena_arena.contracts import canonical_hash
    path = directory / "decisions.json"
    decisions = json.loads(path.read_text())
    change(decisions)
    previous = ""
    for record, snapshot in zip(decisions["records"], decisions["decision_snapshots"], strict=True):
        record["previous_hash"] = previous
        record["record_hash"] = canonical_hash({key: value for key, value in record.items() if key != "record_hash"})
        snapshot["decision_hash"] = record["record_hash"]
        previous = record["record_hash"]
    data = (json.dumps(decisions, sort_keys=True, indent=2) + "\n").encode()
    path.write_bytes(data)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifacts"]["decisions.json"] = hashlib.sha256(data).hexdigest()
    manifest["ledger_hash"] = previous
    manifest["result_hash"] = canonical_hash(decisions["records"])
    manifest["manifest_hash"] = canonical_hash({key: value for key, value in manifest.items() if key != "manifest_hash"})
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")


@pytest.mark.parametrize("filename,change", [
    ("decisions.json", lambda value: value.update(ledger_hash="forged")),
    ("decisions.json", lambda value: value.update(ledger_verified=False)),
    ("evaluation.json", lambda value: value["descriptive"].update(decision_count=999)),
    ("evaluation.json", lambda value: value["descriptive"].update(visible_evidence_count=999)),
])
def test_rejects_rebound_redundant_summary_fields_without_mutation(tmp_path, capsys, filename, change):
    output = tmp_path / "experiment"
    create_experiment(_scenario_text(), "case.json", output, BaselineA())
    _rewrite_bound_artifact(output, filename, change)
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    with pytest.raises(ValueError, match="ledger hash|verification flag|descriptive counts"):
        verify_experiment(output)
    assert main(["inspect", "--experiment-dir", str(output)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "FAIL"
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before


@pytest.mark.parametrize("count,visible", [(1, 0), (3, 2)])
def test_accepts_bound_descriptive_counts_for_zero_or_multiple_decisions(tmp_path, count, visible):
    scenario = json.loads(_scenario_text())
    if visible == 0:
        scenario["timeline"] = ["2026-01-01T00:00:00+00:00"]
        scenario["evidence"] = []
    else:
        timestamp = "2026-01-01T00:00:00+00:00"
        scenario["timeline"] = [timestamp] * count
        scenario["evidence"] = [
            {"evidence_id": str(index), "source_id": str(index), "event_date": timestamp,
             "document_date": timestamp, "verified_available_at": timestamp, "observed_at": timestamp,
             "claims": {}}
            for index in range(visible)
        ]
    output = tmp_path / "experiment"
    create_experiment(json.dumps(scenario), "case.json", output, BaselineA())
    _, files = verify_experiment(output)
    assert files["evaluation.json"]["descriptive"] == {
        "decision_count": count, "visible_evidence_count": visible,
    }
    assert replay_experiment(output, BaselineA())["status"] == "PASS"


def test_rejects_unsupported_and_malformed_config_even_with_consistent_hashes(tmp_path):
    output = tmp_path / "unsupported"
    create_experiment(_scenario_text(), "case.json", output, BaselineA())
    _rewrite_bound_artifact(output, "config.json", lambda config: config.update(policy_id="UNSUPPORTED"))
    with pytest.raises(ValueError, match="unsupported policy"):
        verify_experiment(output)

    second = tmp_path / "malformed"
    create_experiment(_scenario_text(), "case.json", second, BaselineA())
    _rewrite_bound_artifact(second, "input.json", lambda saved: saved.update(input_text=None))
    with pytest.raises(ValueError, match="malformed required fields"):
        verify_experiment(second)


def test_rejects_cross_artifact_scenario_binding_with_updated_hashes(tmp_path):
    output = tmp_path / "experiment"
    create_experiment(_scenario_text(), "case.json", output, BaselineA())
    _rewrite_bound_artifact(output, "config.json", lambda config: config.update(scenario_id="wrong"))
    with pytest.raises(ValueError, match="scenario bindings"):
        verify_experiment(output)


@pytest.mark.parametrize("field,value", [
    ("time", "2026-01-02T00:00:00+00:00"),
    ("scenario_id", "forged"),
    ("seed", 999),
    ("visible_evidence_ids", ["missing"]),
])
def test_rejects_policy_input_binding_mutation_even_with_recomputed_hashes(tmp_path, field, value):
    output = tmp_path / "experiment"
    create_experiment(_scenario_text(), "case.json", output, BaselineA())
    _rewrite_bound_artifact(output, "decisions.json", lambda decisions: decisions["decision_snapshots"][0]["policy_input"].update({field: value}))
    with pytest.raises(ValueError, match="policy_input|evidence snapshot"):
        verify_experiment(output)


def test_preserves_scenario_evidence_order_when_ledger_ids_are_sorted(tmp_path):
    timestamp = "2026-01-01T00:00:00+00:00"
    scenario = json.loads(_scenario_text())
    scenario["timeline"] = [timestamp]
    scenario["evidence"] = [
        {"evidence_id": evidence_id, "source_id": evidence_id, "event_date": timestamp,
         "document_date": timestamp, "verified_available_at": timestamp, "observed_at": timestamp, "claims": {}}
        for evidence_id in ("z", "a")
    ]
    output = tmp_path / "ordered"
    create_experiment(json.dumps(scenario), "case.json", output, BaselineA())
    _, files = verify_experiment(output)
    snapshot = files["decisions.json"]["decision_snapshots"][0]["policy_input"]
    assert [item["evidence_id"] for item in snapshot["visible_evidence"]] == ["z", "a"]
    assert files["decisions.json"]["records"][0]["visible_evidence_ids"] == ["a", "z"]
    assert replay_experiment(output, BaselineA())["status"] == "PASS"


def test_rejects_truncated_or_reordered_timeline_with_recomputed_hashes(tmp_path):
    output = tmp_path / "experiment"
    create_experiment(_scenario_text(), "case.json", output, BaselineA())
    _rewrite_decisions_with_consistent_ledger(output, lambda decisions: decisions.update(
        records=list(reversed(decisions["records"])),
        decision_snapshots=list(reversed(decisions["decision_snapshots"])),
    ))
    with pytest.raises(ValueError, match="timeline"):
        verify_experiment(output)


def test_malformed_visible_evidence_item_fails_as_value_error_and_cli_fail(tmp_path, capsys):
    output = tmp_path / "experiment"
    create_experiment(_scenario_text(), "case.json", output, BaselineA())
    _rewrite_bound_artifact(
        output, "decisions.json",
        lambda decisions: decisions["decision_snapshots"][0]["policy_input"]["visible_evidence"].append(None),
    )
    with pytest.raises(ValueError, match="objects"):
        verify_experiment(output)
    assert main(["inspect", "--experiment-dir", str(output)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "FAIL"


@pytest.mark.parametrize("policy_id,version,parameters", [
    ("UNSUPPORTED", "1.0", {}), ("BASELINE_A", "9.0", {}), ("BASELINE_A", "1.0", {"threshold": 2}),
])
def test_create_rejects_unsupported_policy_before_directory_or_execution(tmp_path, policy_id, version, parameters):
    class Unsupported:
        def __init__(self): self.called = False
        def __call__(self, state):
            self.called = True
            raise AssertionError("must not run")
    policy = Unsupported()
    policy.policy_id, policy.version, policy.parameters = policy_id, version, parameters
    target = tmp_path / "not-created"
    with pytest.raises(ValueError, match="unsupported policy"):
        create_experiment(_scenario_text(), "case.json", target, policy, policy_id)
    assert not target.exists()
    assert not policy.called


def test_replay_rejects_policy_mismatch_before_running(tmp_path):
    output = tmp_path / "experiment"
    create_experiment(_scenario_text(), "case.json", output, BaselineA())
    class Wrong:
        policy_id, version = "OTHER", "1.0"
        def __call__(self, state): raise AssertionError("must not run")
    with pytest.raises(ValueError, match="unsupported policy"):
        replay_experiment(output, Wrong())


def test_source_identity_tracks_whole_worktree_and_validates_loaded_metadata(monkeypatch, tmp_path):
    sibling_dirty = " M src/athena_arena/changed.py\n"
    commands = []
    def fake_run(args, **kwargs):
        commands.append(args)
        if "ls-files" in args:
            return runner.subprocess.CompletedProcess(args, 0, "src/athena_procurement_arena/__init__.py", "")
        if "rev-parse" in args:
            return runner.subprocess.CompletedProcess(args, 0, "a" * 40, "")
        return runner.subprocess.CompletedProcess(args, 0, sibling_dirty, "")
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    class Distribution:
        version = "7.8"
        files = [Path("not/the/loaded/module.py")]
        def locate_file(self, item): return tmp_path / item
        def read_text(self, name): return None
    monkeypatch.setattr(runner.importlib.metadata, "distributions", lambda **kwargs: [Distribution()])
    assert runner.source_identity()["git_dirty"] is True
    assert runner.source_identity()["package_version"] is None
    assert any("status" in args and "--porcelain" in args for args in commands)


def test_source_identity_accepts_matching_wheel_and_editable_metadata(monkeypatch, tmp_path):
    module_path = Path(runner.__file__).resolve()
    class Distribution:
        version = "2.3"
        files = [module_path]
        def locate_file(self, item): return item
        def read_text(self, name): return None
    monkeypatch.setattr(runner.importlib.metadata, "distributions", lambda **kwargs: [Distribution()])
    assert runner.source_identity()["package_version"] == "2.3"
    editable = tmp_path / "project"
    source_package = editable / "src" / "athena_procurement_arena"
    source_package.mkdir(parents=True)
    class Editable(Distribution):
        files = []
        def read_text(self, name): return json.dumps({"url": editable.as_uri(), "dir_info": {"editable": True}})
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda name: type("Spec", (), {"origin": str(source_package / "runner.py")})())
    monkeypatch.setattr(runner.importlib.metadata, "distributions", lambda **kwargs: [Editable()])
    assert runner._loaded_distribution_version(source_package) == "2.3"


def test_saved_early_visible_evidence_hides_later_review_and_inspect_never_executes(tmp_path, monkeypatch):
    scenario = ScenarioDsl.loads(_scenario_text())
    early = replace(scenario.evidence[0], source_spans=("span",))
    reviewed_early = replace(early, action_support=ActionSupportAttestation(
        "p", "PREPARE", "reviewer", scenario.timeline[1], "span", "reviewed later"))
    scenario = replace(scenario, evidence=(reviewed_early, scenario.evidence[1]))
    source = ScenarioDsl.dumps(scenario)
    output = tmp_path / "experiment"
    create_experiment(source, "case.json", output, BaselineA())
    _, files = verify_experiment(output)
    snapshots = files["decisions.json"]["decision_snapshots"]
    assert snapshots[0]["policy_input"]["visible_evidence"][0]["action_support"] is None
    assert snapshots[1]["policy_input"]["visible_evidence"][0]["action_support"]["reviewer"] == "reviewer"
    assert snapshots[1]["policy_input"]["visible_evidence_ids"] != snapshots[0]["policy_input"]["visible_evidence_ids"]
    monkeypatch.setattr(runner, "TemporalWorld", lambda *a, **k: (_ for _ in ()).throw(AssertionError("world ran")))
    monkeypatch.setattr(BaselineA, "__call__", lambda *a, **k: (_ for _ in ()).throw(AssertionError("policy ran")))
    assert verify_experiment(output)[0]["manifest_hash"]


def test_source_identity_uses_loaded_distribution_and_not_unrelated_cwd_repo(monkeypatch, tmp_path):
    calls = []
    def fake_run(args, **kwargs):
        calls.append(args)
        if "ls-files" in args:
            return runner.subprocess.CompletedProcess(args, 1, "", "")
        return runner.subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    class Unrelated:
        version = "0.1.0"
        files = [Path("another/package.py")]
        def locate_file(self, item): return tmp_path / item
        def read_text(self, name): return None
    monkeypatch.setattr(runner.importlib.metadata, "distributions", lambda **kwargs: [Unrelated()])
    identity = runner.source_identity()
    assert identity["package_version"] is None
    assert identity["git_commit"] is None and identity["git_dirty"] is None
    assert any("ls-files" in call for call in calls)


@pytest.mark.parametrize("link_kind", ["experiment", "parent", "manifest"])
def test_rejects_symlinked_paths_before_following_them(tmp_path, link_kind):
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks unavailable")
    real = tmp_path / "real" / "experiment"
    real.parent.mkdir()
    create_experiment(_scenario_text(), "case.json", real, BaselineA())
    alias_parent = tmp_path / "alias-parent"
    experiment_link = tmp_path / "experiment-link"
    try:
        alias_parent.symlink_to(real.parent, target_is_directory=True)
        experiment_link.symlink_to(real, target_is_directory=True)
        if link_kind == "manifest":
            (real / "manifest.json").rename(real / "manifest-real.json")
            (real / "manifest.json").symlink_to(real / "manifest-real.json")
    except OSError as exc:
        if getattr(exc, "winerror", None) == 1314:
            monkeypatch = pytest.MonkeyPatch()
            supplied = {"experiment": real, "parent": real, "manifest": real}[link_kind]
            monkeypatch.setattr(runner, "_contains_symlink", lambda path: link_kind in {"experiment", "parent"})
            if link_kind == "manifest":
                monkeypatch.setattr(Path, "is_symlink", lambda self: self.name == "manifest.json")
            with pytest.raises(ValueError, match="directory|manifest"):
                verify_experiment(supplied)
            monkeypatch.undo()
            return
        raise
    target = {"experiment": experiment_link, "parent": alias_parent / "experiment", "manifest": real}[link_kind]
    with pytest.raises(ValueError, match="directory|manifest"):
        verify_experiment(target)
