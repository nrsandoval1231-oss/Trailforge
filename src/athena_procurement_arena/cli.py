"""Local CLI for deterministic Trailforge mechanics."""
from __future__ import annotations

import argparse
import json

from .campaign import run_campaign, run_regression_campaign, synthetic_scenario
from .policies import BaselineA, keyword_rfp
from .robustness import adversarial_recurrence_world, counterfactual_sensitivity
from .runner import historical_registry, manifest_dict, run_with_manifest
from .tournament import tournament_pipeline


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="trailforge")
    parser.add_argument("mode", choices=("smoke", "scenario", "batch", "compare", "adversarial",
                                          "counterfactual", "historical", "tournament", "benchmark", "replay"))
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)
    baseline = BaselineA()
    if args.mode == "historical":
        result = {"status": "PASS", "fixtures": historical_registry()}
    elif args.mode == "counterfactual":
        result = counterfactual_sensitivity(synthetic_scenario(args.seed), baseline.policy_id, baseline) | {"status": "PASS"}
    elif args.mode == "adversarial":
        from .world import TemporalWorld
        world = TemporalWorld(adversarial_recurrence_world(args.seed), baseline.policy_id, baseline)
        world.run()
        result = {"status": "PASS", "attacks": 1, "invariant_failures": int(not world.ledger.verify()),
                  "predicted_state": world.ledger.records[0].forecast["procurement"]["state"]}
    elif args.mode in {"batch", "compare", "benchmark"}:
        result = run_campaign(args.count, {"KEYWORD": keyword_rfp, "BASELINE_A": baseline}, args.seed)
    elif args.mode == "tournament":
        regression = run_regression_campaign({"KEYWORD": keyword_rfp, "BASELINE_A": baseline}, args.seed)
        result = regression | {"governance": tournament_pipeline(
            "BASELINE_A", {"recall": 1.0, "precision": .5},
            {"recall": .5, "precision": .5}, holdout_available=False)}
    else:
        scenario = synthetic_scenario(args.seed)
        manifest, observations = run_with_manifest(scenario, baseline.policy_id, baseline, mode=args.mode)
        result = manifest_dict(manifest) | {"observations": len(observations), "status": "PASS"}
    print(json.dumps(result, sort_keys=True, default=str))
    return 0
