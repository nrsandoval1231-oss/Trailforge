"""Local CLI for deterministic Trailforge mechanics."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from .campaign import run_campaign, run_regression_campaign, synthetic_scenario
from .fixtures import current_target_fixtures, load_bundle
from .identity_review import load_identity_reviews, resolve_traces, write_resolved_traces
from .policies import BaselineA, keyword_rfp
from .prospective_seal import (
    evaluate_cohort,
    load_seal,
    seal_prospective_outcome,
    write_cohort,
    write_seal,
)
from .public_capture import capture_with_firecrawl, load_capture, write_capture
from .retrospective_seal import (
    TraceOutcomeState,
    build_outcome_cohort,
    seal_trace_outcome,
    write_outcome_cohort,
    write_outcome_seal,
)
from .rfp_intake import screen_aura_rental_candidate
from .robustness import adversarial_recurrence_world, counterfactual_sensitivity
from .runner import historical_registry, manifest_dict, run_with_manifest
from .shadow import load_shadow_record
from .signal_ledger import SignalType
from .signal_review import accept_candidate, candidate_from_capture, write_signal
from .tournament import tournament_pipeline
from .trace_backtest import backtest_cohort, backtest_traces, load_traces, write_backtest, write_cohort_backtest
from .trace_cohort import build_trace_cohort, write_trace_cohort


def _next_action(reason_codes: tuple[str, ...], *, current: bool) -> str:
    """Map fail-closed screen reasons to a deterministic operator action."""
    if not current:
        return "ARCHIVE_OR_MONITOR_LIFECYCLE"
    if not reason_codes:
        return "HUMAN_REVIEW_FOR_NEXT_STEP"
    if "CAPACITY_EVIDENCE_IS_RATING_OR_AGGREGATE_ONLY" in reason_codes:
        return "VERIFY_PER_PROJECT_REQUIRED_CAPACITY"
    if any(code.endswith("NOT_CAPTURED") or code.endswith("UNSUPPORTED") for code in reason_codes):
        return "VERIFY_MISSING_SOURCE_REQUIREMENT"
    if "INCOMPATIBLE_FUEL" in reason_codes:
        return "REJECT_INCOMPATIBLE_FUEL"
    if any(code.endswith("BELOW_MINIMUM") for code in reason_codes):
        return "REJECT_BELOW_MINIMUM"
    if any("REJECTED" in code or "SCOPE" in code for code in reason_codes):
        return "REJECT_OUT_OF_SCOPE"
    return "HUMAN_REVIEW_FOR_NEXT_STEP"


def _screen_bundle(bundle) -> dict:
    """Return an explainable, provenance-bearing screen for every fixture."""
    records = []
    for item in bundle.fixtures:
        screen = screen_aura_rental_candidate(item.scenario.evidence)
        if not item.current:
            disposition = "NOT_CURRENT"
            reason_codes = ("OPPORTUNITY_NOT_CURRENT",)
        else:
            disposition = str(screen.status)
            reason_codes = screen.reason_codes
        records.append({
            "fixture_id": item.fixture_id,
            "source_url": item.source_url,
            "retrieved_at": item.retrieved_at,
            "verified_by": item.verified_by,
            "opportunity_status": item.opportunity_status,
            "disposition": disposition,
            "reason_codes": list(reason_codes),
            "next_action": _next_action(reason_codes, current=item.current),
            "screen": screen.as_dict(),
            "verification_notes": item.verification_notes,
        })
    counts = {key: sum(item["disposition"] == key for item in records)
              for key in ("QUALIFIED", "NEEDS_REVIEW", "REJECTED", "NOT_CURRENT")}
    return {"status": "PASS", "mode": "screen-bundle", "bundle_id": bundle.bundle_id,
            "count": len(records), "counts": counts, "fixtures": records}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="trailforge")
    parser.add_argument("mode", choices=("smoke", "unit", "scenario", "batch", "compare", "adversarial",
                                          "counterfactual", "historical", "tournament", "benchmark", "replay",
                                          "optimize", "shortlist", "validate-bundle",
                                          "screen-bundle", "capture-public", "review-signal", "backtest-traces", "backtest-cohort", "resolve-traces", "build-trace-cohort", "seal-trace-outcome", "build-outcome-cohort", "seal-prospective", "evaluate-cohort"))
    parser.add_argument("--bundle", help="versioned local fixture bundle for shortlist mode")
    parser.add_argument("--url", help="one public HTTP(S) URL for capture-public")
    parser.add_argument("--capture-id", help="stable capture identifier for capture-public")
    parser.add_argument("--captured-by", help="operator identity for capture-public")
    parser.add_argument("--capture", help="raw capture JSON for review-signal")
    parser.add_argument("--signal-id", help="stable signal ID for review-signal")
    parser.add_argument("--project-id", help="exact project identity for review-signal")
    parser.add_argument("--signal-type", choices=[item.value for item in SignalType])
    parser.add_argument("--signal-title", help="reviewed signal title")
    parser.add_argument("--observed-at", help="signal observation timestamp")
    parser.add_argument("--source-quote", help="exact quote from the raw capture")
    parser.add_argument("--claims-json", default="{}", help="JSON claims for review-signal")
    parser.add_argument("--reviewed-by", help="named reviewer for review-signal")
    parser.add_argument("--traces", nargs="+", help="trace JSON files for backtest-traces")
    parser.add_argument("--target-type", choices=[item.value for item in SignalType])
    parser.add_argument("--early-types", nargs="+", choices=[item.value for item in SignalType])
    parser.add_argument("--identity-reviews", help="hash-bound identity review JSON for resolve-traces")
    parser.add_argument("--cohort", help="verified trace cohort manifest for backtest-cohort")
    parser.add_argument("--trace", help="reviewed trace JSON for seal-trace-outcome")
    parser.add_argument("--seal-id", help="seal identifier for seal-trace-outcome")
    parser.add_argument("--outcome-state", choices=[item.value for item in TraceOutcomeState])
    parser.add_argument("--target-signal-id", help="observed target signal ID for seal-trace-outcome")
    parser.add_argument("--cutoff-at", help="timezone-aware cutoff timestamp for seal-trace-outcome")
    parser.add_argument("--source-sha256", help="evidence SHA-256 for seal-trace-outcome")
    parser.add_argument("--reviewer-statement", help="explicit reviewer outcome statement")
    parser.add_argument("--reviewed-at", help="timezone-aware review timestamp")
    parser.add_argument("--source-url", help="public evidence URL for outcome seal")
    parser.add_argument("--source-ref", help="confidential evidence reference for outcome seal")
    parser.add_argument("--trace-cohort-hash", help="verified trace cohort hash for outcome cohort")
    parser.add_argument("--outcome-seals", nargs="+", help="outcome seal JSON files for build-outcome-cohort")
    parser.add_argument("--cohort-id", help="cohort identifier for build-trace-cohort / evaluate-cohort")
    parser.add_argument("--assembled-by", help="reviewer identity for build-trace-cohort")
    parser.add_argument("--assembled-at", help="timezone-aware ISO timestamp for build-trace-cohort")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--shadow", help="path to prospective shadow record JSON for seal-prospective")
    parser.add_argument("--outcome", help="verified outcome state for seal-prospective")
    parser.add_argument("--verified-by", help="reviewer name for seal-prospective / evaluate-cohort")
    parser.add_argument("--verified-at", help="ISO timestamp for seal-prospective (default now)")
    parser.add_argument("--output", help="output path for seal-prospective / evaluate-cohort")
    parser.add_argument("--seals", nargs="+", help="paths to sealed outcome JSON files for evaluate-cohort")
    parser.add_argument("--floor-accuracy", type=float, default=0.0, help="minimum cohort accuracy floor")
    parser.add_argument("--incumbent-accuracy", type=float, default=0.0, help="incumbent cohort accuracy")
    args = parser.parse_args(argv)
    baseline = BaselineA()
    if args.mode == "seal-trace-outcome":
        required = (args.trace, args.seal_id, args.target_type, args.outcome_state, args.cutoff_at,
                    args.source_sha256, args.source_quote, args.reviewer_statement, args.reviewed_by,
                    args.reviewed_at, args.output)
        if not all(required):
            parser.error("seal-trace-outcome requires --trace, --seal-id, --target-type, --outcome-state, "
                         "--cutoff-at, --source-sha256, --source-quote, --reviewer-statement, --reviewed-by, "
                         "--reviewed-at, and --output")
        from .signal_ledger import EvidenceClass, load_trace
        seal = seal_trace_outcome(load_trace(args.trace), seal_id=args.seal_id,
                                  target_signal_type=SignalType(args.target_type),
                                  cutoff_at=datetime.fromisoformat(args.cutoff_at),
                                  outcome_state=TraceOutcomeState(args.outcome_state),
                                  source_sha256=args.source_sha256, source_quote=args.source_quote,
                                  reviewer_statement=args.reviewer_statement, reviewed_by=args.reviewed_by,
                                  reviewed_at=datetime.fromisoformat(args.reviewed_at),
                                  evidence_class=EvidenceClass.PUBLIC if args.source_url else EvidenceClass.CONFIDENTIAL,
                                  source_url=args.source_url, source_ref=args.source_ref,
                                  target_signal_id=args.target_signal_id)
        write_outcome_seal(seal, args.output)
        result = {"status": "PASS", "mode": "seal-trace-outcome", "seal_id": seal.seal_id,
                  "seal_hash": seal.seal_hash, "outcome_state": seal.outcome_state, "output": args.output}
    elif args.mode == "build-outcome-cohort":
        if not args.outcome_seals or not args.cohort_id or not args.trace_cohort_hash or not args.target_type or not args.assembled_by or not args.assembled_at or not args.output:
            parser.error("build-outcome-cohort requires --outcome-seals, --cohort-id, --trace-cohort-hash, "
                         "--target-type, --assembled-by, --assembled-at, and --output")
        cohort = build_outcome_cohort(args.outcome_seals, cohort_id=args.cohort_id,
                                      trace_cohort_hash=args.trace_cohort_hash,
                                      target_signal_type=SignalType(args.target_type),
                                      created_by=args.assembled_by,
                                      created_at=datetime.fromisoformat(args.assembled_at))
        write_outcome_cohort(cohort, args.output)
        result = {"status": "PASS", "mode": "build-outcome-cohort", "cohort_id": cohort.cohort_id,
                  "cohort_hash": cohort.cohort_hash, "observed_count": cohort.observed_count,
                  "not_observed_count": cohort.not_observed_count, "inconclusive_count": cohort.inconclusive_count,
                  "output": args.output}
    elif args.mode == "backtest-cohort":
        if not args.cohort or not args.target_type or not args.early_types or not args.output:
            parser.error("backtest-cohort requires --cohort, --target-type, --early-types, and --output")
        report = backtest_cohort(args.cohort, target_signal_type=SignalType(args.target_type),
                                 early_signal_types=tuple(SignalType(item) for item in args.early_types))
        write_cohort_backtest(report, args.output)
        result = {"status": "PASS", "mode": "backtest-cohort", "cohort_id": report.cohort_id,
                  "cohort_hash": report.cohort_hash, "report_hash": report.report_hash,
                  "coverage": report.report.coverage, "output": args.output}
    elif args.mode == "build-trace-cohort":
        if not args.traces or not args.cohort_id or not args.assembled_by or not args.assembled_at or not args.output:
            parser.error("build-trace-cohort requires --traces, --cohort-id, --assembled-by, --assembled-at, and --output")
        manifest = build_trace_cohort(args.traces, cohort_id=args.cohort_id, assembled_by=args.assembled_by,
                                      assembled_at=datetime.fromisoformat(args.assembled_at))
        write_trace_cohort(manifest, args.output)
        result = {"status": "PASS", "mode": "build-trace-cohort", "cohort_id": manifest.cohort_id,
                  "project_count": manifest.project_count, "cohort_hash": manifest.cohort_hash,
                  "output": args.output}
    elif args.mode == "resolve-traces":
        if not args.traces or not args.identity_reviews or not args.output:
            parser.error("resolve-traces requires --traces, --identity-reviews, and --output")
        resolved = resolve_traces(load_traces(args.traces), load_identity_reviews(args.identity_reviews))
        write_resolved_traces(resolved, args.output)
        result = {"status": "PASS", "mode": "resolve-traces", "trace_count": len(resolved),
                  "signal_count": sum(len(trace.signals) for trace in resolved), "output": args.output}
    elif args.mode == "backtest-traces":
        if not args.traces or not args.target_type or not args.early_types or not args.output:
            parser.error("backtest-traces requires --traces, --target-type, --early-types, and --output")
        report = backtest_traces(
            load_traces(args.traces), target_signal_type=SignalType(args.target_type),
            early_signal_types=tuple(SignalType(item) for item in args.early_types),
        )
        write_backtest(report, args.output)
        result = {"status": "PASS", "mode": "backtest-traces", "report_hash": report.report_hash,
                  "coverage": report.coverage, "target_cases": report.target_cases,
                  "matched_cases": report.matched_cases, "output": args.output}
    elif args.mode == "review-signal":
        required = (args.capture, args.signal_id, args.project_id, args.signal_type, args.signal_title,
                    args.observed_at, args.source_quote, args.reviewed_by, args.output)
        if not all(required):
            parser.error("review-signal requires --capture, --signal-id, --project-id, --signal-type, "
                         "--signal-title, --observed-at, --source-quote, --reviewed-by, and --output")
        capture = load_capture(args.capture)
        candidate = candidate_from_capture(
            capture, candidate_id=f"candidate-{args.signal_id}", project_id=args.project_id,
            observed_at=datetime.fromisoformat(args.observed_at), signal_type=SignalType(args.signal_type),
            title=args.signal_title, source_quote=args.source_quote,
            claims=json.loads(args.claims_json), proposed_by=args.reviewed_by,
        )
        signal = accept_candidate(candidate, capture, signal_id=args.signal_id, reviewed_by=args.reviewed_by)
        write_signal(signal, args.output)
        result = {"status": "PASS", "mode": "review-signal", "signal_id": signal.signal_id,
                  "signal_hash": signal.signal_hash, "output": args.output}
    elif args.mode == "capture-public":
        if not args.url or not args.capture_id or not args.captured_by or not args.output:
            parser.error("capture-public requires --url, --capture-id, --captured-by, and --output")
        capture = capture_with_firecrawl(args.url, capture_id=args.capture_id, captured_by=args.captured_by)
        write_capture(capture, args.output)
        result = {"status": "PASS", "mode": "capture-public", "capture_id": capture.capture_id,
                  "source_url": capture.source_url, "content_sha256": capture.content_sha256,
                  "capture_hash": capture.capture_hash, "output": args.output}
    elif args.mode == "optimize":
        from .athena_optimizer import run_athena_optimization
        result = run_athena_optimization(seed=args.seed)
    elif args.mode in {"shortlist", "screen-bundle", "validate-bundle"}:
        if not args.bundle:
            parser.error(f"{args.mode} requires --bundle <path>")
        bundle = load_bundle(args.bundle)
        if args.mode == "validate-bundle":
            result = {"status": "PASS", "mode": args.mode, "bundle_id": bundle.bundle_id,
                      "fixtures": len(bundle.fixtures), "holdout_available": bundle.sealed_holdout_available}
            print(json.dumps(result, sort_keys=True, default=str))
            return 0
        if args.mode == "screen-bundle":
            result = _screen_bundle(bundle)
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
        suite = Path(__file__).resolve().parents[2] / "tests" / "procurement_arena"
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(suite)],
            capture_output=True,
            text=True,
            check=False,
        )
        result = {
            "status": "PASS" if completed.returncode == 0 else "FAIL",
            "suite": str(suite),
            "returncode": completed.returncode,
            "output": completed.stdout.strip(),
        }
    elif args.mode in {"batch", "compare", "benchmark"}:
        result = run_campaign(args.count, {"KEYWORD": keyword_rfp, "BASELINE_A": baseline}, args.seed)
    elif args.mode == "tournament":
        regression = run_regression_campaign({"KEYWORD": keyword_rfp, "BASELINE_A": baseline}, args.seed)
        result = regression | {"governance": tournament_pipeline(
            "BASELINE_A", {"recall": 1.0, "precision": .5},
            {"recall": .5, "precision": .5}, holdout_available=False)}
    elif args.mode == "seal-prospective":
        if not args.shadow or not args.outcome or not args.verified_by or not args.output:
            parser.error("seal-prospective requires --shadow, --outcome, --verified-by, and --output")
        shadow = load_shadow_record(args.shadow)
        verified_at = datetime.fromisoformat(args.verified_at) if args.verified_at else datetime.now(UTC)
        seal = seal_prospective_outcome(
            shadow,
            seal_id=Path(args.output).stem,
            verified_outcome=args.outcome,
            verified_at=verified_at,
            verified_by=args.verified_by,
        )
        write_seal(seal, args.output)
        result = {"status": "PASS", "mode": "seal-prospective", "seal_id": seal.seal_id,
                  "seal_hash": seal.seal_hash, "output": args.output}
    elif args.mode == "evaluate-cohort":
        if not args.seals or not args.cohort_id or not args.output:
            parser.error("evaluate-cohort requires --seals, --cohort-id, and --output")
        seals = tuple(load_seal(item) for item in args.seals)
        cohort = evaluate_cohort(
            args.cohort_id,
            seals,
            floors={"accuracy": args.floor_accuracy},
            incumbent_metrics={"accuracy": args.incumbent_accuracy, "incorrect": len(seals)},
        )
        write_cohort(cohort, args.output)
        result = {"status": "PASS", "mode": "evaluate-cohort", "cohort_id": cohort.cohort_id,
                  "metrics": cohort.metrics, "governance": cohort.governance, "output": args.output}
    else:
        scenario = synthetic_scenario(args.seed)
        manifest, observations = run_with_manifest(scenario, baseline.policy_id, baseline, mode=args.mode)
        result = manifest_dict(manifest) | {"observations": len(observations), "status": "PASS"}
    print(json.dumps(result, sort_keys=True, default=str))
    return 0 if result["status"] == "PASS" else 1
