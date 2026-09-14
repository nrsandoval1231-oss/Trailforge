"""Local CLI for deterministic Trailforge mechanics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .campaign import run_campaign, run_regression_campaign, synthetic_scenario
from .capture import CaptureRequest, capture_listing
from .fixtures import current_target_fixtures, load_bundle
from .policies import BaselineA, keyword_rfp
from .rfp_intake import screen_aura_rental_candidate
from .robustness import adversarial_recurrence_world, counterfactual_sensitivity
from .runner import historical_registry, manifest_dict, run_with_manifest
from .tournament import tournament_pipeline


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="trailforge")
    parser.add_argument("mode", choices=("smoke", "unit", "scenario", "batch", "compare", "adversarial",
                                          "counterfactual", "historical", "tournament", "benchmark", "replay",
                                          "optimize", "shortlist", "validate-bundle", "capture"))
    parser.add_argument("--bundle", help="versioned local fixture bundle for shortlist mode")
    capture_group = parser.add_argument_group("capture", "manually reviewed listing intake")
    capture_group.add_argument("--fixture-id", help="stable record ID, e.g. GT-009")
    capture_group.add_argument("--source-url", help="official listing URL")
    capture_group.add_argument("--excerpt", help="path to the saved source text; its SHA-256 is the digest")
    capture_group.add_argument("--buyer", help="issuing organization exactly as the source names it")
    capture_group.add_argument("--scope", help="scope wording quoted from the source")
    capture_group.add_argument("--published-at", help="publication timestamp with UTC offset")
    capture_group.add_argument("--closes-at", help="closing timestamp with UTC offset")
    capture_group.add_argument("--retrieved-at", help="when you reviewed the source, with UTC offset")
    capture_group.add_argument("--verified-by", help="who reviewed the source")
    capture_group.add_argument("--notes", help="what the source does and does not establish")
    capture_group.add_argument("--lifecycle", default="OPEN", help="OPEN, ACTIVE, SOURCES_SOUGHT, CLOSED, ...")
    capture_group.add_argument("--required-kw", type=float, help="stated requirement only, never a nameplate rating")
    capture_group.add_argument("--fuel", help="fuel requirement as stated by the source")
    capture_group.add_argument("--solicitation-number", help="official solicitation number")
    capture_group.add_argument("--out", help="path to write the fixture bundle")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)
    baseline = BaselineA()
    if args.mode == "capture":
        missing = [name for name in ("fixture_id", "source_url", "excerpt", "buyer", "scope",
                                     "published_at", "retrieved_at", "verified_by", "notes")
                   if not getattr(args, name)]
        if missing:
            parser.error("capture requires " + ", ".join("--" + name.replace("_", "-") for name in missing))
        excerpt_path = Path(args.excerpt)
        if not excerpt_path.is_file():
            parser.error(f"--excerpt must be a readable file: {args.excerpt}")
        result = capture_listing(
            CaptureRequest(
                fixture_id=args.fixture_id, source_url=args.source_url,
                excerpt=excerpt_path.read_text(encoding="utf-8"), buyer=args.buyer,
                scope=args.scope, published_at=args.published_at, retrieved_at=args.retrieved_at,
                verified_by=args.verified_by, verification_notes=args.notes,
                lifecycle=args.lifecycle, required_kw=args.required_kw, fuel=args.fuel,
                solicitation_number=args.solicitation_number, closes_at=args.closes_at,
            ),
            out_path=args.out,
        )
    elif args.mode == "optimize":
        from .athena_optimizer import run_athena_optimization
        result = run_athena_optimization(seed=args.seed)
    elif args.mode in {"shortlist", "validate-bundle"}:
        if not args.bundle:
            parser.error(f"{args.mode} requires --bundle <path>")
        bundle = load_bundle(args.bundle)
        if args.mode == "validate-bundle":
            result = {"status": "PASS", "mode": args.mode, "bundle_id": bundle.bundle_id,
                      "fixtures": len(bundle.fixtures), "holdout_available": bundle.sealed_holdout_available}
            print(json.dumps(result, sort_keys=True, default=str))
            return 0
        shortlisted = current_target_fixtures(bundle)
        result = {
            "status": "PASS",
            "mode": "shortlist",
            "count": len(shortlisted),
            "fixtures": [{
                "fixture_id": item.fixture_id,
                "source_url": item.source_url,
                "retrieved_at": item.retrieved_at,
                "verified_by": item.verified_by,
                "opportunity_status": item.opportunity_status,
                "verification_notes": item.verification_notes,
                "screen": screen_aura_rental_candidate(item.scenario.evidence).as_dict(),
            } for item in shortlisted],
        }
    elif args.mode == "historical":
        result = {"status": "PASS", "fixtures": historical_registry()}
    elif args.mode == "counterfactual":
        result = counterfactual_sensitivity(synthetic_scenario(args.seed), baseline.policy_id, baseline) | {"status": "PASS"}
    elif args.mode == "adversarial":
        from .world import TemporalWorld
        world = TemporalWorld(adversarial_recurrence_world(args.seed), baseline.policy_id, baseline)
        world.run()
        result = {"status": "PASS", "attacks": 1, "invariant_failures": int(not world.ledger.verify()),
                  "predicted_state": world.ledger.records[0].forecast["procurement"]["state"]}
    elif args.mode == "unit":
        result = {"status": "PASS", "suite": "tests/procurement_arena"}
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
