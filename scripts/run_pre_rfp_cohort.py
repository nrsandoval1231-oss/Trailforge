"""Offline replay of reviewed historical case manifests."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from athena_arena.contracts import canonical_hash  # noqa: E402
from athena_procurement_arena.historical_cases import (  # noqa: E402
    load_case,
    replay_case,
    validate_family_splits,
    write_replay_result,
)
from athena_procurement_arena.policies import BaselineA  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="+", required=True, help="case.json manifests")
    parser.add_argument("--mode", choices=("BACKTRACE", "DISCOVERY"), required=True)
    parser.add_argument("--experiment-root", required=True, help="new or existing directory for per-case baseline runs")
    parser.add_argument("--output", required=True, help="new cohort result JSON")
    args = parser.parse_args(argv)

    loaded = [load_case(path) for path in args.cases]
    cases = [item[0] for item in loaded]
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("cohort contains duplicate case IDs")
    validate_family_splits(cases)
    results = []
    experiment_root = Path(args.experiment_root)
    for path, (case, _) in zip(args.cases, loaded, strict=True):
        result = replay_case(path, mode=args.mode, policy=BaselineA(),
                            experiment_dir=experiment_root / case.case_id)
        result.update({"facility_type": case.facility_type, "power_activity": case.power_activity,
                       "purchase_type": case.purchase_type, "holdout_group": case.holdout_group})
        results.append(result)
    summary = {
        "schema_version": "trailforge-pre-rfp-cohort-replay-v1",
        "mode": args.mode,
        "discovery_credit": False,
        "discovery_credit_reason": "SLICE_A_REQUIRES_PROSPECTIVE_PRECOMMITTED_NAME_BLIND_VALIDATION",
        "case_count": len(results),
        "positive_count": sum(case.outcome in {"RELEVANT_PROCUREMENT_OBSERVED", "PRIVATE_BUYING_EVENT_VERIFIED"}
                              for case in cases),
        "negative_count": sum(case.outcome in {"CANCELED", "DELAYED", "SUPPLY_RESOLVED", "INCOMPATIBLE_SOLUTION",
                                               "AWARDED_BEFORE_DETECTION", "GENERATION_NOT_IN_SCOPE"}
                              for case in cases),
        "unresolved_count": sum(case.outcome in {"UNKNOWN", "NO_OUTCOME_OBSERVED"} for case in cases),
        "vertical_counts": dict(sorted(Counter(case.facility_type for case in cases).items())),
        "pre_rfp_baseline_surface_count": sum(item["pre_rfp_first_surface_at"] is not None for item in results),
        "baseline_a_surface_count": sum(item["baseline_first_surface_at"] is not None for item in results),
        "supported_historical_lead_count": sum(item["lead_status"] == "SUPPORTED" for item in results),
        "unknown_availability_count": sum(item["unknown_availability_count"] for item in results),
        "results": results,
    }
    summary["cohort_hash"] = canonical_hash(summary)
    write_replay_result(summary, args.output)
    print(json.dumps({"status": "PASS", "mode": args.mode, "case_count": len(results),
                      "cohort_hash": summary["cohort_hash"], "output": str(Path(args.output).resolve())},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
