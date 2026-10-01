"""Reproducible run manifests and historical fixture boundaries."""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from athena_arena.contracts import canonical_hash

from .foundation import Scenario
from .scenario_dsl import ScenarioDsl
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
    metrics: dict[str, Any] = None
    invariant_results: dict[str, Any] = None
    artifact_paths: tuple[str, ...] = ()

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

EXPERIMENT_ARTIFACTS = ("input.json", "decisions.json", "evaluation.json", "config.json")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, default=_json_default) + "\n").encode()


def _json_default(value: Any) -> Any:
    from dataclasses import is_dataclass
    from enum import Enum
    if is_dataclass(value):
        return {key: getattr(value, key) for key in value.__dataclass_fields__}
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (tuple, frozenset)):
        return list(value)
    if isinstance(value, dict):
        return value
    if hasattr(value, "items"):
        return dict(value.items())
    raise TypeError(f"unsupported JSON value {type(value).__name__}")


def _jsonable_evidence(event: Any, decision_time: datetime) -> dict[str, Any]:
    from dataclasses import replace
    visible_event = replace(event, action_support=None) if (
        event.action_support is not None and event.action_support.reviewed_at > decision_time
    ) else event
    return json.loads(_json_bytes(visible_event))


def source_identity() -> dict[str, Any]:
    """Identify the loaded package tree without consulting the caller's cwd."""
    package = Path(__file__).resolve().parent
    root = package.parent
    files = sorted([*package.glob("*.py"), *(root / "athena_arena").glob("*.py")])
    digest = hashlib.sha256()
    for item in files:
        digest.update(item.relative_to(root).as_posix().encode() + b"\0")
        digest.update(item.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    # Attribute Git only when the loaded package files are tracked by this repo.
    repo = next((parent for parent in package.parents if (parent / ".git").exists()), None)
    commit, dirty = None, None
    if repo is not None:
        try:
            ownership_paths = (
                package.relative_to(repo) / "__init__.py",
                # athena_arena is an implicit namespace package, so its
                # tracked module anchors the second loaded package path.
                (root / "athena_arena").relative_to(repo) / "contracts.py",
            )
            tracked = subprocess.run(
                ["git", "-C", str(repo), "ls-files", "--error-unmatch", *map(str, ownership_paths)],
                capture_output=True, text=True,
            )
            if tracked.returncode == 0:
                commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True,
                                        text=True, check=True).stdout.strip()
                dirty = bool(subprocess.run(["git", "-C", str(repo), "status", "--porcelain"],
                                            capture_output=True, text=True, check=True).stdout.strip())
        except (OSError, subprocess.SubprocessError):
            commit, dirty = None, None
    version = _loaded_distribution_version(package)
    return {"source_content_sha256": digest.hexdigest(), "git_commit": commit, "git_dirty": dirty,
            "package_version": version}


def _loaded_distribution_version(package: Path) -> str | None:
    """Return a distribution version only when its metadata identifies loaded files."""
    spec = importlib.util.find_spec("athena_procurement_arena.runner")
    module_path = Path(spec.origin).resolve() if spec and spec.origin else Path(__file__).resolve()
    try:
        distributions = importlib.metadata.distributions(name="athena-trailforge")
    except (importlib.metadata.PackageNotFoundError, TypeError):
        return None
    for distribution in distributions:
        try:
            files = distribution.files or ()
            if any(Path(distribution.locate_file(item)).resolve() == module_path for item in files):
                return distribution.version
            direct_url = json.loads(distribution.read_text("direct_url.json") or "{}")
            if direct_url.get("dir_info", {}).get("editable"):
                from urllib.parse import unquote, urlparse
                url = direct_url.get("url", "")
                parsed = urlparse(url)
                parsed_path = unquote(parsed.path)
                if parsed.scheme == "file" and re.match(r"^/[A-Za-z]:/", parsed_path):
                    parsed_path = parsed_path[1:]
                project = Path(parsed_path).resolve() if parsed.scheme == "file" else Path(url).resolve()
                if (project / "src" / "athena_procurement_arena").resolve() == package:
                    return distribution.version
        except (OSError, ValueError, TypeError):
            continue
    return None


def _manifest_hash(payload: dict[str, Any]) -> str:
    return canonical_hash({key: value for key, value in payload.items() if key != "manifest_hash"})


def create_experiment(scenario_text: str, source_path: str, directory: str | Path,
                      policy: Any, policy_id: str = "BASELINE_A", *,
                      fixture_context: dict[str, Any] | None = None) -> dict[str, Any]:
    _validate_policy(policy, policy_id)
    scenario = ScenarioDsl.loads(scenario_text)
    if fixture_context is not None:
        _verify_fixture_context(fixture_context, scenario)
    target = Path(directory)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=False, exist_ok=False)
    world = TemporalWorld(scenario, policy_id, policy)
    world.run()
    input_payload = {"source_path": source_path, "input_sha256": hashlib.sha256(scenario_text.encode()).hexdigest(),
                     "input_text": scenario_text, "scenario_id": scenario.scenario_id,
                     "scenario_version": scenario.version, "seed": scenario.seed}
    if fixture_context is not None:
        input_payload["fixture_context"] = fixture_context
    decisions = {"ledger_hash": world.replay_hash(), "ledger_verified": world.ledger.verify(),
                 "records": world.ledger.records, "decision_snapshots": world.decision_snapshots}
    evaluation = {"status": "UNSEALED", "scoring": "UNSCORED",
                  "descriptive": {"decision_count": len(world.ledger.records),
                                  "visible_evidence_count": len(set().union(*(set(r.visible_evidence_ids)
                                                                              for r in world.ledger.records)))} if world.ledger.records else {"decision_count": 0, "visible_evidence_count": 0},
                  "outcome_metrics": "UNAVAILABLE",
                  "declared_truth": {"status": "UNVERIFIED", "values": {
                      "procurement_episode_id": scenario.truth.procurement_episode_id,
                      "outcome": scenario.truth.outcome,
                      "solicitation_at": scenario.truth.solicitation_at.isoformat()
                      if scenario.truth.solicitation_at else None}},
                  "later_evidence": {"status": "UNVERIFIED", "values": [
                      {"evidence_id": item.evidence_id, "source_id": item.source_id,
                       "verified_available_at": item.verified_available_at.isoformat(),
                       "observed_at": item.observed_at.isoformat(), "claims": dict(item.claims)}
                      for item in scenario.evidence]}}
    config = {"policy_id": policy_id, "policy_version": getattr(policy, "version", "UNKNOWN"),
              "policy_parameters": {}, "scenario_id": scenario.scenario_id,
              "scenario_version": scenario.version, "seed": scenario.seed, "source_identity": source_identity()}
    values = {"input.json": input_payload, "decisions.json": decisions,
              "evaluation.json": evaluation, "config.json": config}
    hashes = {}
    for name, value in values.items():
        data = _json_bytes(value)
        with (target / name).open("xb") as stream:
            stream.write(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    manifest = {"schema": "trailforge-experiment-v1", "artifacts": hashes,
                "scenario_hash": world.scenario_hash, "result_hash": world.replay_hash(),
                "ledger_hash": world.ledger.head_hash, "source_identity": config["source_identity"]}
    manifest["manifest_hash"] = _manifest_hash(manifest)
    with (target / "manifest.json").open("xb") as stream:
        stream.write(_json_bytes(manifest))
    return manifest


def _validate_policy(policy: Any, policy_id: str) -> None:
    if (policy_id != "BASELINE_A" or getattr(policy, "policy_id", None) != "BASELINE_A"
            or getattr(policy, "version", None) != "1.0"
            or getattr(policy, "parameters", {}) not in ({}, None)):
        raise ValueError("unsupported policy; BASELINE_A 1.0 with empty parameters is required")


def verify_experiment(directory: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    supplied = Path(directory).absolute()
    if _contains_symlink(supplied) or not supplied.is_dir():
        raise ValueError("experiment path must be a directory")
    target = supplied.resolve(strict=True)
    manifest_path = target / "manifest.json"
    if manifest_path.is_symlink():
        raise ValueError("manifest path is unsafe")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != "trailforge-experiment-v1":
        raise ValueError("invalid experiment manifest schema")
    if (not isinstance(manifest.get("artifacts"), dict)
            or set(manifest.get("artifacts", {})) != set(EXPERIMENT_ARTIFACTS)):
        raise ValueError("experiment manifest required artifact set is invalid")
    if manifest.get("manifest_hash") != _manifest_hash(manifest):
        raise ValueError("experiment manifest hash mismatch")
    loaded = {}
    for name in EXPERIMENT_ARTIFACTS:
        path = target / name
        if path.is_symlink() or not path.is_file() or path.resolve().parent != target:
            raise ValueError(f"required artifact missing or unsafe: {name}")
        data = path.read_bytes()
        if not isinstance(manifest["artifacts"][name], str) or hashlib.sha256(data).hexdigest() != manifest["artifacts"][name]:
            raise ValueError(f"artifact hash mismatch: {name}")
        loaded[name] = json.loads(data)
    if not isinstance(loaded["decisions.json"], dict) or not isinstance(loaded["decisions.json"].get("records"), list):
        raise ValueError("invalid decisions artifact schema")
    records = loaded["decisions.json"]["records"]
    previous = ""
    for record in records:
        if not isinstance(record, dict) or record.get("previous_hash") != previous:
            raise ValueError("decision ledger hash chain is invalid")
        payload = {key: value for key, value in record.items() if key != "record_hash"}
        if record.get("record_hash") != canonical_hash(payload):
            raise ValueError("decision ledger record hash mismatch")
        previous = record["record_hash"]
    if previous != manifest.get("ledger_hash") or canonical_hash(records) != manifest.get("result_hash"):
        raise ValueError("decision ledger is not bound to manifest")
    if not isinstance(loaded["evaluation.json"], dict) or loaded["evaluation.json"].get("status") != "UNSEALED":
        raise ValueError("invalid evaluation artifact schema")
    if not isinstance(loaded["config.json"], dict) or not isinstance(loaded["input.json"], dict):
        raise ValueError("invalid config or input artifact schema")
    config, saved_input, evaluation = loaded["config.json"], loaded["input.json"], loaded["evaluation.json"]
    if (config.get("policy_id") != "BASELINE_A" or config.get("policy_version") != "1.0"
            or config.get("policy_parameters") != {}):
        raise ValueError("unsupported policy configuration; BASELINE_A 1.0 with empty parameters is required")
    if (not isinstance(saved_input.get("input_text"), str)
            or not isinstance(saved_input.get("input_sha256"), str)
            or not isinstance(saved_input.get("source_path"), str)
            or not isinstance(saved_input.get("scenario_id"), str)
            or not isinstance(saved_input.get("scenario_version"), str)
            or isinstance(saved_input.get("seed"), bool) or not isinstance(saved_input.get("seed"), int)):
        raise ValueError("input artifact has malformed required fields")
    if hashlib.sha256(saved_input["input_text"].encode()).hexdigest() != saved_input["input_sha256"]:
        raise ValueError("input content hash mismatch")
    try:
        scenario = ScenarioDsl.loads(saved_input["input_text"])
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("saved input scenario is malformed") from exc
    if (config.get("scenario_id") != scenario.scenario_id or config.get("scenario_version") != scenario.version
            or config.get("seed") != scenario.seed or saved_input.get("scenario_id") != scenario.scenario_id
            or saved_input.get("scenario_version") != scenario.version or saved_input.get("seed") != scenario.seed
            or manifest.get("scenario_hash") != canonical_hash(scenario)):
        raise ValueError("input, config and manifest scenario bindings do not match")
    source = config.get("source_identity")
    if (not isinstance(source, dict) or not isinstance(source.get("source_content_sha256"), str)
            or source != manifest.get("source_identity")):
        raise ValueError("source identity binding mismatch")
    if (not isinstance(evaluation, dict) or evaluation.get("status") != "UNSEALED"
            or evaluation.get("scoring") != "UNSCORED" or evaluation.get("outcome_metrics") != "UNAVAILABLE"):
        raise ValueError("invalid unsealed evaluation semantics")
    if "fixture_context" in saved_input:
        _verify_fixture_context(saved_input["fixture_context"], scenario)
    truth = scenario.truth
    if evaluation.get("declared_truth") != {"status": "UNVERIFIED", "values": {
            "procurement_episode_id": truth.procurement_episode_id, "outcome": truth.outcome,
            "solicitation_at": truth.solicitation_at.isoformat() if truth.solicitation_at else None}}:
        raise ValueError("evaluation retained truth does not match saved input")
    expected_evidence = [{"evidence_id": item.evidence_id, "source_id": item.source_id,
                          "verified_available_at": item.verified_available_at.isoformat(),
                          "observed_at": item.observed_at.isoformat(), "claims": dict(item.claims)}
                         for item in scenario.evidence]
    if evaluation.get("later_evidence") != {"status": "UNVERIFIED", "values": expected_evidence}:
        raise ValueError("evaluation retained evidence does not match saved input")
    expected_timeline = [item.isoformat() for item in scenario.timeline]
    descriptive = evaluation.get("descriptive")
    visible_count = len({evidence_id for record in records
                         for evidence_id in record.get("visible_evidence_ids", [])})
    if (not isinstance(descriptive, dict)
            or type(descriptive.get("decision_count")) is not int
            or type(descriptive.get("visible_evidence_count")) is not int
            or descriptive["decision_count"] != len(records)
            or descriptive["visible_evidence_count"] != visible_count):
        raise ValueError("evaluation descriptive counts do not match verified records")
    if len(records) != len(expected_timeline) or [record.get("simulation_time") if isinstance(record, dict) else None
                                                   for record in records] != expected_timeline:
        raise ValueError("decision ledger timeline does not match saved scenario")
    decisions = loaded["decisions.json"]
    if (decisions.get("ledger_hash") != canonical_hash(records)
            or decisions.get("ledger_hash") != manifest.get("result_hash")):
        raise ValueError("decision artifact ledger hash does not match verified records")
    if decisions.get("ledger_verified") is not True:
        raise ValueError("decision artifact ledger verification flag is invalid")
    snapshots = loaded["decisions.json"].get("decision_snapshots")
    if not isinstance(snapshots, list) or len(snapshots) != len(records):
        raise ValueError("decision snapshot count mismatch")
    evidence_by_id = {item.evidence_id: item for item in scenario.evidence}
    for record, snapshot in zip(records, snapshots, strict=True):
        if (not isinstance(snapshot, dict) or snapshot.get("decision_hash") != record["record_hash"]
                or snapshot.get("action") != record["action"]
                or snapshot.get("policy_id") != record["policy_id"]
                or snapshot.get("decision_time") != record["simulation_time"]
                or snapshot.get("policy_output") != record["forecast"]):
            raise ValueError("decision snapshot binding mismatch")
        policy_input = snapshot.get("policy_input")
        if not isinstance(policy_input, dict):
            raise ValueError("decision policy_input must be an object")
        timestamp = record.get("simulation_time")
        if (policy_input.get("time") != timestamp or policy_input.get("scenario_id") != scenario.scenario_id
                or policy_input.get("seed") != scenario.seed):
            raise ValueError("decision policy_input time or scenario binding mismatch")
        visible_ids = record.get("visible_evidence_ids")
        if (not isinstance(visible_ids, list) or policy_input.get("visible_evidence_ids") != visible_ids):
            raise ValueError("decision policy_input visible evidence binding mismatch")
        visible = policy_input.get("visible_evidence")
        if not isinstance(visible, list) or any(not isinstance(item, dict) for item in visible):
            raise ValueError("decision policy_input evidence snapshot must contain objects")
        snapshot_ids = [item.get("evidence_id") for item in visible]
        if (any(not isinstance(evidence_id, str) for evidence_id in snapshot_ids)
                or len(snapshot_ids) != len(set(snapshot_ids))
                or set(snapshot_ids) != set(visible_ids)):
            raise ValueError("decision policy_input evidence snapshot does not match ledger")
        if record.get("scenario_id") != scenario.scenario_id or record.get("policy_id") != config.get("policy_id"):
            raise ValueError("decision record scenario or policy identity mismatch")
        try:
            decision_time = datetime.fromisoformat(timestamp)
        except (TypeError, ValueError) as exc:
            raise ValueError("decision record time is malformed") from exc
        expected_ids = sorted(item.evidence_id for item in scenario.evidence if item.visible_at(decision_time))
        if visible_ids != expected_ids:
            raise ValueError("decision evidence does not match scenario timeline")
        expected_visible = [item for item in scenario.evidence if item.visible_at(decision_time)]
        if snapshot_ids != [item.evidence_id for item in expected_visible]:
            raise ValueError("decision evidence snapshot order does not match saved scenario")
        for item, original in zip(visible, expected_visible, strict=True):
            evidence_id = item["evidence_id"]
            if evidence_by_id.get(evidence_id) != original:
                raise ValueError("decision evidence is absent or unavailable at decision time")
            if original.verified_available_at > decision_time:
                raise ValueError("decision evidence is absent or unavailable at decision time")
            expected = _jsonable_evidence(original, decision_time)
            if item != expected:
                raise ValueError("decision evidence snapshot does not match retained scenario")
    return manifest, loaded


def _verify_fixture_context(context: Any, scenario: Scenario) -> None:
    """Verify retained bundle bytes and selected fixture without source access."""
    from .fixtures import load_bundle_mapping
    if (not isinstance(context, dict) or context.get("input_kind") != "fixture_bundle"
            or not isinstance(context.get("bundle_text"), str)
            or not isinstance(context.get("bundle_sha256"), str)
            or not isinstance(context.get("bundle_source_path"), str)
            or not isinstance(context.get("fixture_id"), str)):
        raise ValueError("fixture context is malformed")
    bundle_text = context["bundle_text"]
    if hashlib.sha256(bundle_text.encode()).hexdigest() != context["bundle_sha256"]:
        raise ValueError("retained fixture bundle hash mismatch")
    try:
        raw = json.loads(bundle_text)
        if not isinstance(raw, dict):
            raise ValueError("bundle must be an object")
        bundle = load_bundle_mapping(raw)
    except (ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        raise ValueError("retained fixture bundle is malformed") from exc
    selected = [item for item in bundle.fixtures if item.fixture_id == context["fixture_id"]]
    if len(selected) != 1:
        raise ValueError("retained fixture selection is missing or ambiguous")
    if selected[0].scenario != scenario:
        raise ValueError("selected fixture scenario does not match retained input")
    if context.get("bundle_id") != bundle.bundle_id or context.get("bundle_version") != bundle.version:
        raise ValueError("fixture bundle context binding mismatch")
    if (not isinstance(context.get("fixture"), dict)
            or context["fixture"] != selected[0].as_dict()):
        raise ValueError("selected fixture provenance context does not match retained bundle")


def _contains_symlink(path: Path) -> bool:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            return True
    return False


def replay_experiment(directory: str | Path, policy: Any) -> dict[str, Any]:
    manifest, files = verify_experiment(directory)
    _validate_policy(policy, files["config.json"]["policy_id"])
    actual_source = source_identity()
    source_match = actual_source["source_content_sha256"] == manifest["source_identity"].get("source_content_sha256")
    scenario = ScenarioDsl.loads(files["input.json"]["input_text"])
    world = TemporalWorld(scenario, files["config.json"]["policy_id"], policy)
    world.run()
    checks = {"source_content": source_match, "scenario_hash": world.scenario_hash == manifest["scenario_hash"],
              "result_hash": world.replay_hash() == manifest["result_hash"],
              "ledger": world.ledger.verify(),
              "input_binding": hashlib.sha256(files["input.json"]["input_text"].encode()).hexdigest() == files["input.json"]["input_sha256"]}
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "manifest_hash": manifest["manifest_hash"]}


def historical_registry() -> tuple[dict[str, str], ...]:
    return tuple({"fixture_id": key, "name": name, "status": "UNVERIFIED", "scoreable": "false"}
                 for key, name in HISTORICAL_FIXTURES.items())


def historical_replay(fixture_id: str, *, status: str = "UNVERIFIED") -> dict[str, Any]:
    """Return a replay gate; current discoverability never implies historical availability."""
    if fixture_id not in HISTORICAL_FIXTURES:
        raise KeyError(f"unknown historical fixture: {fixture_id}")
    if status != "SEALED_READY":
        return {"fixture_id": fixture_id, "status": status, "scoreable": False,
                "reason": "timeline and verified availability are not sealed"}
    return {"fixture_id": fixture_id, "status": "SEALED_READY", "scoreable": True}


def run_with_manifest(scenario: Scenario, policy_id: str, policy: Any, *, experiment_id: str = "run-001",
                      mode: str = "scenario", config: dict[str, Any] | None = None,
                      created_at: datetime | None = None) -> tuple[RunManifest, tuple[Any, ...]]:
    world = TemporalWorld(scenario, policy_id, policy)
    observations = world.run()
    try:
        source_commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                                      check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - only non-git copies
        source_commit = "UNCOMMITTED_LOCAL"
    final_state = world.ledger.records[-1].forecast.get("procurement", {}).get("state", "UNKNOWN") if world.ledger.records else "UNKNOWN"
    manifest = RunManifest(experiment_id, mode, world.scenario_hash, policy_id, scenario.seed,
        (created_at or datetime.now(UTC)).isoformat(), source_commit, config or {},
        {"python": sys.version.split()[0], "platform": platform.platform()}, world.replay_hash(),
        {"decision_count": len(world.ledger.records), "final_procurement_state": final_state},
        {"ledger": world.ledger.verify()}, ())
    return manifest, observations


def manifest_dict(manifest: RunManifest) -> dict[str, Any]:
    return asdict(manifest) | {"manifest_hash": manifest.manifest_hash}


def verify_replay(manifest: RunManifest, scenario: Scenario, policy: Any) -> dict[str, Any]:
    """Verify an existing manifest against a fresh deterministic replay."""
    world = TemporalWorld(scenario, manifest.policy_id, policy)
    world.run()
    try:
        current_commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                                        check=True).stdout.strip()
        source_commit_matches = (re.fullmatch(r"[0-9a-f]{40}", current_commit) is not None
                                 and current_commit == manifest.source_commit)
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - non-git copies
        source_commit_matches = False
    checks = {"scenario_hash": world.scenario_hash == manifest.scenario_hash,
              "result_hash": world.replay_hash() == manifest.result_hash,
              "source_commit": source_commit_matches}
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "manifest_hash": manifest.manifest_hash}


def write_manifest(manifest: RunManifest, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest_dict(manifest), sort_keys=True, indent=2), encoding="utf-8")
    return target


def load_manifest(path: str | Path) -> RunManifest:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    stored_hash = raw.pop("manifest_hash", None)
    if not isinstance(stored_hash, str) or re.fullmatch(r"[0-9a-f]{64}", stored_hash) is None:
        raise ValueError("manifest_hash is missing or malformed")
    if "artifact_paths" in raw:
        raw["artifact_paths"] = tuple(raw["artifact_paths"])
    manifest = RunManifest(**raw)
    if manifest.manifest_hash != stored_hash:
        raise ValueError("manifest_hash does not match manifest contents")
    return manifest
