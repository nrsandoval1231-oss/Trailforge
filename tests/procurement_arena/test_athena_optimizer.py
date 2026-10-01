import shutil

import pytest

from athena_procurement_arena.athena_optimizer import (
    _arena_source_inventory,
    _default_arena_source_roots,
    _evaluation_context_fingerprint,
    _robustness_pass,
    evaluate_policy,
    run_athena_optimization,
    weighted_threshold_policy,
)
from athena_procurement_arena.governance import CandidateLesson, NegativeKnowledge
from athena_procurement_arena.policies import BaselineA


def test_athena_evaluation_is_family_complete_and_deterministic():
    left = evaluate_policy("BASELINE_A", BaselineA(), seed=7)
    right = evaluate_policy("BASELINE_A", BaselineA(), seed=7)
    assert left == right
    assert left["runs"] == 40
    assert left["invariant_failures"] == 0


def test_athena_loop_quarantines_without_holdout_and_emits_artifacts():
    result = run_athena_optimization(seed=7)
    assert result["status"] == "PASS"
    assert result["promotion_count"] == 0
    assert len(result["candidates"]) == 7
    assert result["search_space"] == {"weighted_thresholds": [2, 4, 6]}
    for item in result["candidates"].values():
        assert item["metrics"]["invariant_failures"] == 0
        assert item["gates"]["outcome"] in {"REJECT", "QUARANTINE"}
        assert item["candidate_policy"]["self_promoted"] is False


def test_athena_skips_loaded_exact_rejected_lesson_and_preserves_other_candidates(monkeypatch, tmp_path):
    initial = run_athena_optimization(seed=7)
    rejected = CandidateLesson(**initial["candidates"]["KEYWORD"]["lesson"])
    store = NegativeKnowledge()
    store.reject(rejected)
    snapshot = tmp_path / "negative-knowledge.json"
    store.save(snapshot)
    loaded_store = NegativeKnowledge.load(snapshot)
    tournament_calls = []
    evaluation_calls = []
    robustness_calls = []
    policy_calls = []
    import athena_procurement_arena.athena_optimizer as optimizer
    real_tournament = optimizer.tournament_pipeline
    real_evaluate = optimizer.evaluate_policy
    real_robustness = optimizer._robustness_pass
    real_candidate_policy = optimizer.CandidatePolicy

    def track_tournament(candidate_id, *args, **kwargs):
        tournament_calls.append(candidate_id)
        return real_tournament(candidate_id, *args, **kwargs)

    def track_evaluation(policy_id, *args, **kwargs):
        evaluation_calls.append(policy_id)
        return real_evaluate(policy_id, *args, **kwargs)

    def track_robustness(policy_id, *args, **kwargs):
        robustness_calls.append(policy_id)
        return real_robustness(policy_id, *args, **kwargs)

    def track_candidate_policy(candidate_id, *args, **kwargs):
        policy_calls.append(candidate_id)
        return real_candidate_policy(candidate_id, *args, **kwargs)

    monkeypatch.setattr(optimizer, "tournament_pipeline", track_tournament)
    monkeypatch.setattr(optimizer, "evaluate_policy", track_evaluation)
    monkeypatch.setattr(optimizer, "_robustness_pass", track_robustness)
    monkeypatch.setattr(optimizer, "CandidatePolicy", track_candidate_policy)
    result = run_athena_optimization(seed=7, negative_knowledge=loaded_store)
    assert result["status"] == "PASS"
    assert result["candidates"]["KEYWORD"]["status"] == "SKIPPED"
    assert result["candidates"]["KEYWORD"]["skip_reason"] == "REJECTED_IDEA"
    assert len(result["candidates"]["KEYWORD"]["lesson_digest"]) == 64
    assert result["skipped_candidates"]["KEYWORD"] == "REJECTED_IDEA"
    assert "KEYWORD" not in evaluation_calls
    assert "KEYWORD" not in robustness_calls
    assert "KEYWORD" not in policy_calls
    assert "KEYWORD" not in tournament_calls
    assert len(result["candidates"]) == 7
    assert all(key in result["candidates"] for key in tournament_calls)
    assert result["promotion_count"] == 0


def test_athena_does_not_skip_changed_lesson_with_same_id():
    initial = run_athena_optimization(seed=7)
    original = CandidateLesson(**initial["candidates"]["KEYWORD"]["lesson"])
    changed = CandidateLesson(original.lesson_id, "changed hypothesis", original.supporting_cohort,
                              original.counterexamples, original.affected_policy, original.proposed_change,
                              original.expected_effect, original.risks)
    store = NegativeKnowledge()
    store.reject(changed)
    result = run_athena_optimization(seed=7, negative_knowledge=store)
    assert result["status"] == "CONFLICT"
    assert result["candidates"]["KEYWORD"]["status"] == "CONFLICT"
    assert result["candidates"]["KEYWORD"]["skip_reason"] == "REJECTED_IDENTITY_CONFLICT"
    assert result["conflicts"]["KEYWORD"] == "REJECTED_IDENTITY_CONFLICT"


def test_athena_preflight_conflicts_when_seed_changes():
    initial = run_athena_optimization(seed=7)
    rejected = CandidateLesson(**initial["candidates"]["KEYWORD"]["lesson"])
    store = NegativeKnowledge()
    store.reject(rejected)
    result = run_athena_optimization(seed=8, negative_knowledge=store)
    assert result["candidates"]["KEYWORD"]["status"] == "CONFLICT"
    assert result["candidates"]["KEYWORD"]["skip_reason"] == "REJECTED_IDENTITY_CONFLICT"
    assert "KEYWORD" in result["conflicts"]


def test_athena_preflight_conflicts_when_evaluation_source_changes(monkeypatch):
    initial = run_athena_optimization(seed=7)
    rejected = CandidateLesson(**initial["candidates"]["KEYWORD"]["lesson"])
    store = NegativeKnowledge()
    store.reject(rejected)
    import athena_procurement_arena.athena_optimizer as optimizer
    monkeypatch.setattr(optimizer, "_evaluation_context_fingerprint", lambda seed: "changed-context")
    result = run_athena_optimization(seed=7, negative_knowledge=store)
    assert result["candidates"]["KEYWORD"]["status"] == "CONFLICT"
    assert result["candidates"]["KEYWORD"]["skip_reason"] == "REJECTED_IDENTITY_CONFLICT"


def test_arena_source_inventory_includes_world_and_foundation():
    inventory = _arena_source_inventory()
    assert inventory is not None
    paths = {(entry["package"], entry["path"]) for entry in inventory}
    assert ("athena_procurement_arena", "world.py") in paths
    assert ("athena_procurement_arena", "foundation.py") in paths
    assert any(package == "athena_arena" for package, _ in paths)


@pytest.mark.parametrize("changed_path", ["world.py", "foundation.py"])
def test_arena_source_fingerprint_changes_for_world_and_foundation_copy(tmp_path, changed_path):
    original_roots = _default_arena_source_roots()
    copied_roots = {}
    for package, root in original_roots.items():
        copied = tmp_path / package
        shutil.copytree(root, copied)
        copied_roots[package] = copied
    before = _evaluation_context_fingerprint(7, package_roots=copied_roots)
    assert before is not None
    changed_source = copied_roots["athena_procurement_arena"] / changed_path
    changed_source.write_text(changed_source.read_text(encoding="utf-8") + "\n# changed test copy\n", encoding="utf-8")
    after = _evaluation_context_fingerprint(7, package_roots=copied_roots)
    assert after is not None
    assert after != before


def test_loaded_store_conflicts_when_world_source_copy_changes(monkeypatch, tmp_path):
    initial = run_athena_optimization(seed=7)
    rejected = CandidateLesson(**initial["candidates"]["KEYWORD"]["lesson"])
    store = NegativeKnowledge()
    store.reject(rejected)
    snapshot = tmp_path / "negative-knowledge.json"
    store.save(snapshot)
    loaded_store = NegativeKnowledge.load(snapshot)

    copied_roots = {}
    for package, root in _default_arena_source_roots().items():
        copied = tmp_path / package
        shutil.copytree(root, copied)
        copied_roots[package] = copied
    world_source = copied_roots["athena_procurement_arena"] / "world.py"
    world_source.write_text(world_source.read_text(encoding="utf-8") + "\n# changed test copy\n", encoding="utf-8")
    import athena_procurement_arena.athena_optimizer as optimizer
    monkeypatch.setattr(optimizer, "_default_arena_source_roots", lambda: copied_roots)

    result = run_athena_optimization(seed=7, negative_knowledge=loaded_store)
    assert result["status"] == "CONFLICT"
    assert result["candidates"]["KEYWORD"]["status"] == "CONFLICT"
    assert result["candidates"]["KEYWORD"]["skip_reason"] == "REJECTED_IDENTITY_CONFLICT"


def test_missing_arena_source_root_cannot_produce_reusable_context(tmp_path):
    roots = _default_arena_source_roots()
    roots["athena_arena"] = tmp_path / "missing-shared-package"
    assert _evaluation_context_fingerprint(7, package_roots=roots) is None


def test_athena_conflicts_when_source_fingerprint_unavailable(monkeypatch):
    initial = run_athena_optimization(seed=7)
    rejected = CandidateLesson(**initial["candidates"]["KEYWORD"]["lesson"])
    store = NegativeKnowledge()
    store.reject(rejected)
    import athena_procurement_arena.athena_optimizer as optimizer
    monkeypatch.setattr(optimizer, "_evaluation_context_fingerprint", lambda seed: None)
    result = run_athena_optimization(seed=7, negative_knowledge=store)
    assert result["candidates"]["KEYWORD"]["status"] == "CONFLICT"
    assert result["candidates"]["KEYWORD"]["skip_reason"] == "REJECTED_IDENTITY_CONFLICT"


def test_weighted_threshold_is_bounded_and_tunable():
    with pytest.raises(ValueError):
        weighted_threshold_policy(-1)
    low = evaluate_policy("WEIGHTED_T2", weighted_threshold_policy(2), seed=7)
    high = evaluate_policy("WEIGHTED_T6", weighted_threshold_policy(6), seed=7)
    assert low["runs"] == high["runs"] == 40
    assert low["invariant_failures"] == high["invariant_failures"] == 0
    assert low["alerts"] >= high["alerts"]


def test_athena_counterfactual_gate_rejects_confidence_only_response():
    def confidence_only(state):
        extension_seen = any(
            "contract_extension" in item.claims for item in state["visible_evidence"]
        )
        confidence = 0.2 if extension_seen else 0.1
        return {"procurement": {"state": "UNKNOWN", "confidence": confidence},
                "power": {"status": "UNKNOWN", "peak_gap_mw": None}}, "IGNORE"

    adversarial_pass, counterfactual_pass = _robustness_pass("CONFIDENCE_ONLY", confidence_only, 9)
    assert adversarial_pass is True
    assert counterfactual_pass is False
