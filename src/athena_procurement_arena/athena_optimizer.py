"""Deterministic Athena adapter for bounded policy optimization."""
from __future__ import annotations

import hashlib
import inspect
import json
import marshal
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .campaign import synthetic_scenario
from .evaluation import evaluate_replay
from .governance import AthenaInput, CandidateLesson, CandidatePolicy, NegativeKnowledge
from .policies import (
    BaselineA,
    buyer_frequency,
    classify_target,
    keyword_rfp,
    latest_event,
    static_weighted_score,
)
from .robustness import adversarial_recurrence_world, counterfactual_suite
from .scenarios import SCENARIO_FAMILIES, family_scenario
from .tournament import tournament_pipeline
from .world import TemporalWorld

Policy = Callable[[Mapping[str, Any]], tuple[dict[str, Any], str]]

_EVALUATION_CONTEXT_PATHS: dict[str, Path] = {__name__: Path(__file__)}
for _context_function in (
    evaluate_replay, family_scenario, adversarial_recurrence_world,
    counterfactual_suite, synthetic_scenario, tournament_pipeline,
):
    _context_module = inspect.getmodule(_context_function)
    _context_path = inspect.getsourcefile(_context_module) if _context_module is not None else None
    if _context_module is not None and _context_path is not None:
        _EVALUATION_CONTEXT_PATHS[_context_module.__name__] = Path(_context_path)


def _policy_fingerprint(policy: Policy) -> str | None:
    """Bind a preflight idea to its implementation module and captured config."""
    code = getattr(policy, "__code__", None)
    source_path = inspect.getsourcefile(policy)
    if code is None or source_path is None:
        return None
    try:
        closure = [cell.cell_contents for cell in (getattr(policy, "__closure__", None) or ())]
        captures = json.dumps(
            {"defaults": getattr(policy, "__defaults__", None), "closure": closure},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
        module_digest = hashlib.sha256(Path(source_path).read_bytes()).digest()
        code_digest = marshal.dumps((code.co_code, code.co_consts, code.co_names, code.co_varnames))
    except (OSError, TypeError, ValueError, AttributeError):
        return None
    return hashlib.sha256(module_digest + code_digest + captures).hexdigest()


def _evaluation_context_fingerprint(seed: int) -> str | None:
    """Bind idea reuse to the exact run seed and evaluation/gate source context."""
    module_digests: dict[str, str] = {}
    for module_name, source_path in _EVALUATION_CONTEXT_PATHS.items():
        try:
            module_digests[module_name] = hashlib.sha256(source_path.read_bytes()).hexdigest()
        except OSError:
            return None
    context = {
        "seed": seed,
        "scenario_families": list(SCENARIO_FAMILIES),
        "modules": module_digests,
    }
    try:
        serialized = json.dumps(context, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def weighted_threshold_policy(threshold: int) -> Policy:
    """Build a policy whose only tunable parameter is the action threshold."""
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    weights = {"capital": 2, "funded": 2, "permit": 1, "engineering": 1, "rfp": 4, "budget": 2}

    def policy(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
        target = classify_target(tuple(state.get("visible_evidence", ())))
        if target != "IN_SCOPE_PRIME_POWER_300KW_PLUS":
            return {"scope": target, "score": 0, "threshold": threshold}, "IGNORE"
        text = " ".join(
            str(item.get("claims", {}) if isinstance(item, Mapping) else getattr(item, "claims", {})).lower()
            for item in state.get("visible_evidence", ())
        )
        score = sum(weight for word, weight in weights.items() if word in text)
        action = "PREPARE" if score >= threshold and score else ("RESEARCH" if score else "IGNORE")
        return {"score": score, "threshold": threshold}, action

    return policy


def evaluate_policy(policy_id: str, policy: Policy, *, seed: int = 1) -> dict[str, Any]:
    """Evaluate a policy on every registered family without using future evidence."""
    rows = []
    invariant_failures = 0
    for index, family in enumerate(SCENARIO_FAMILIES):
        scenario = family_scenario(family, seed + index)
        world = TemporalWorld(scenario, policy_id, policy)
        world.run()
        invariant_failures += int(not world.ledger.verify())
        rows.append(evaluate_replay(scenario, world.ledger.records))
    recalls = [float(row.discovery["recall"]) for row in rows]
    precisions = [float(row.discovery["precision"] or 0.0) for row in rows]
    actionable = sum(int(row.action["actionable_steps"] or 0) for row in rows)
    attention = sum(int(row.action["attention_burden"] or 0) for row in rows)
    count = len(rows)
    return {
        "runs": count,
        "invariant_failures": invariant_failures,
        "recall": round(sum(recalls) / count, 6),
        "precision": round(sum(precisions) / count, 6),
        "alerts": actionable,
        "cost": attention,
        "actionable_steps": actionable,
    }


def _robustness_pass(policy_id: str, policy: Policy, seed: int) -> tuple[bool, bool]:
    adversarial = TemporalWorld(adversarial_recurrence_world(seed), policy_id, policy)
    adversarial.run()
    adversarial_pass = adversarial.ledger.verify() and all(
        record.forecast.get("procurement", {}).get("state", "UNKNOWN") == "UNKNOWN"
        and record.action not in {"RESEARCH", "PREPARE", "BID_REVIEW"}
        for record in adversarial.ledger.records
    )
    cases = counterfactual_suite(synthetic_scenario(seed), policy_id, policy)
    counterfactual_pass = all(case["passed"] for case in cases)
    return adversarial_pass, counterfactual_pass


def run_athena_optimization(*, seed: int = 1, holdout_available: bool = False, fixture_bundle: Any = None,
                            negative_knowledge: NegativeKnowledge | None = None) -> dict[str, Any]:
    """Run Athena's candidate loop; promotion remains human/holdout gated."""
    incumbent_id = "BASELINE_A"
    incumbent: Policy = BaselineA()
    candidates: dict[str, Policy] = {
        "KEYWORD": keyword_rfp,
        "STATIC_WEIGHTED": static_weighted_score,
        "LATEST_EVENT": latest_event,
        "BUYER_FREQUENCY": buyer_frequency,
        **{f"WEIGHTED_T{threshold}": weighted_threshold_policy(threshold) for threshold in (2, 4, 6)},
    }
    incumbent_metrics = evaluate_policy(incumbent_id, incumbent, seed=seed)
    evaluation_context = _evaluation_context_fingerprint(seed)
    results: dict[str, Any] = {}
    for candidate_id, policy in candidates.items():
        lesson_id = f"lesson-{candidate_id.lower()}"
        hypothesis = f"Evaluate whether {candidate_id} improves evidence efficiency over {incumbent_id}."
        policy_fingerprint = _policy_fingerprint(policy)
        proposed_change = {
            "candidate_policy": candidate_id,
            "policy_fingerprint": policy_fingerprint,
            "evaluation_context_fingerprint": evaluation_context,
        }
        if negative_knowledge is not None:
            if (policy_fingerprint is None or evaluation_context is None) and negative_knowledge.contains(lesson_id):
                disposition = "CONFLICT"
            else:
                disposition = negative_knowledge.classify_idea(
                    lesson_id, hypothesis, SCENARIO_FAMILIES, incumbent_id, proposed_change,
                )
            if disposition != "NEW":
                stored_lesson = next(item for item in negative_knowledge.lessons if item.lesson_id == lesson_id)
                reason = "REJECTED_IDEA" if disposition == "REJECTED" else "REJECTED_IDENTITY_CONFLICT"
                results[candidate_id] = {
                    "status": "SKIPPED" if disposition == "REJECTED" else "CONFLICT",
                    "skip_reason": reason,
                    "lesson": stored_lesson.__dict__,
                    "lesson_digest": negative_knowledge.lesson_digest(lesson_id),
                }
                continue
        metrics = evaluate_policy(candidate_id, policy, seed=seed)
        adversarial_pass, counterfactual_pass = _robustness_pass(candidate_id, policy, seed)
        lesson = CandidateLesson(
            lesson_id=lesson_id,
            hypothesis=hypothesis,
            supporting_cohort=SCENARIO_FAMILIES,
            counterexamples=tuple(family for family in SCENARIO_FAMILIES if metrics["recall"] < incumbent_metrics["recall"]),
            affected_policy=incumbent_id,
            proposed_change=proposed_change,
            expected_effect={"recall": metrics["recall"], "precision": metrics["precision"]},
        )
        candidate = CandidatePolicy(candidate_id, lesson.lesson_id, "1", {"policy_id": candidate_id})
        gates = tournament_pipeline(
            candidate_id,
            metrics,
            incumbent_metrics,
            invariant_failures=metrics["invariant_failures"],
            floors={"recall": 0.0, "precision": 0.0},
            adversarial_pass=adversarial_pass,
            counterfactual_pass=counterfactual_pass,
            holdout_available=holdout_available,
        )
        results[candidate_id] = {
            "metrics": metrics,
            "athena_input": AthenaInput(
                frozen_state={"seed": seed, "families": len(SCENARIO_FAMILIES)},
                decision={"policy_id": candidate_id},
                forecast={"candidate": candidate_id},
                verified_outcome={"holdout_available": holdout_available},
                evaluation=metrics,
            ).__dict__,
            "lesson": lesson.__dict__,
            "candidate_policy": candidate.__dict__,
            "gates": gates,
        }
        if fixture_bundle is not None:
            from .fixtures import score_fixture_bundle
            results[candidate_id]["verified_holdout"] = score_fixture_bundle(
                candidate_id, policy, fixture_bundle, subset="holdout")
    conflicts = {key: item["skip_reason"] for key, item in results.items() if item.get("status") == "CONFLICT"}
    return {
        "status": "CONFLICT" if conflicts else "PASS",
        "seed": seed,
        "incumbent": {"policy_id": incumbent_id, "metrics": incumbent_metrics},
        "holdout_available": holdout_available,
        "search_space": {"weighted_thresholds": [2, 4, 6]},
        "candidates": results,
        "skipped_candidates": {
            key: item["skip_reason"] for key, item in results.items() if item.get("status") == "SKIPPED"
        },
        "conflicts": conflicts,
        "promotion_count": sum(item.get("gates", {}).get("outcome") == "PROMOTE" for item in results.values()),
    }
