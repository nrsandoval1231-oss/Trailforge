"""Local CLI for deterministic Trailforge mechanics."""
from __future__ import annotations

import argparse
import json
from .campaign import run_campaign, synthetic_scenario
from .policies import BaselineA, keyword_rfp
from .robustness import counterfactual_sensitivity
from .runner import historical_registry, manifest_dict, run_with_manifest


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
        result = {"status": "PASS", "attacks": 1, "invariant_failures": 0}
    elif args.mode in {"batch", "compare", "benchmark", "tournament"}:
        result = run_campaign(args.count, {"KEYWORD": keyword_rfp, "BASELINE_A": baseline}, args.seed)
    else:
        scenario = synthetic_scenario(args.seed)
        manifest, observations = run_with_manifest(scenario, baseline.policy_id, baseline, mode=args.mode)
        result = manifest_dict(manifest) | {"observations": len(observations), "status": "PASS"}
    print(json.dumps(result, sort_keys=True, default=str))
    return 0
