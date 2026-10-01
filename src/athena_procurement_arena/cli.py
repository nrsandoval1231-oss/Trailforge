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
from .retrospective_evaluation import evaluate_retrospective, write_retrospective_evaluation
from .retrospective_seal import (
    TraceOutcomeState,
    build_outcome_cohort,
    load_outcome_cohort,
    seal_trace_outcome,
    write_outcome_cohort,
    write_outcome_seal,
)
from .rfp_candidate_capture import (
    accept_rfp_candidate,
    candidate_from_excerpt,
    load_rfp_candidate,
    write_accepted_rfp_bundle,
    write_rfp_candidate,
)
from .rfp_candidate_queue import build_rfp_candidate_queue, write_rfp_candidate_queue
from .rfp_intake import screen_aura_rental_candidate
from .robustness import adversarial_recurrence_world, counterfactual_sensitivity
from .runner import historical_registry, load_manifest, manifest_dict, run_with_manifest, verify_replay
from .scenario_dsl import ScenarioDsl
from .shadow import load_shadow_record
from .signal_ledger import SignalType
from .signal_review import accept_candidate, candidate_from_capture, write_signal
from .tournament import tournament_pipeline
from .trace_backtest import (
    backtest_cohort,
    backtest_traces,
    load_cohort_backtest,
    load_traces,
    write_backtest,
    write_cohort_backtest,
)
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
                                          "screen-bundle", "capture-public", "review-signal", "capture-rfp-candidate", "accept-rfp-candidate", "build-rfp-review-queue", "backtest-traces", "backtest-cohort", "resolve-traces", "build-trace-cohort", "seal-trace-outcome", "build-outcome-cohort", "evaluate-retrospective", "seal-prospective", "evaluate-cohort"))
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
    parser.add_argument("--candidate", help="hash-bound RFP candidate JSON for accept-rfp-candidate")
    parser.add_argument("--candidate-id", help="stable RFP candidate identifier for capture-rfp-candidate")
    parser.add_argument("--candidates", nargs="+", help="hash-bound RFP candidate JSON files for review queue")
    parser.add_argument("--queue-id", help="stable identifier for an RFP candidate review queue")
    parser.add_argument("--excerpt-file", help="local UTF-8 source excerpt file for RFP candidate capture/review")
    parser.add_argument("--buyer", help="reviewed buyer name for capture-rfp-candidate")
    parser.add_argument("--scope", help="reviewed scope text for capture-rfp-candidate")
    parser.add_argument("--published-at", help="timezone-aware source publication timestamp")
    parser.add_argument("--retrieved-at", help="timezone-aware local retrieval timestamp")
    parser.add_argument("--required-kw", type=float, help="explicit source-backed per-project requirement in kW")
    parser.add_argument("--fuel", help="explicit source-backed fuel requirement")
    parser.add_argument("--solicitation-number", help="source-backed solicitation identifier")
    parser.add_argument("--closes-at", help="timezone-aware source closing timestamp")
    parser.add_argument("--opportunity-status", help="explicit lifecycle for accept-rfp-candidate")
    parser.add_argument("--fixture-id", help="verified fixture identifier for accept-rfp-candidate")
    parser.add_argument("--verification-notes", help="review notes for accept-rfp-candidate")
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
    parser.add_argument("--cohort-backtest", help="cohort-bound backtest JSON for evaluate-retrospective")
    parser.add_argument("--outcome-cohort", help="retrospective outcome cohort JSON for evaluate-retrospective")
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
    parser.add_argument("--scenario-file", help="scenario JSON input for scenario/replay")
    parser.add_argument("--manifest", help="saved run manifest for replay")
    parser.add_argument("--seals", nargs="+", help="paths to sealed outcome JSON files for evaluate-cohort")
    parser.add_argument("--floor-accuracy", type=float, default=0.0, help="minimum cohort accuracy floor")
    parser.add_argument("--incumbent-accuracy", type=float, default=0.0, help="incumbent cohort accuracy")
    args = parser.parse_args(argv)
    baseline = BaselineA()
    scenario_modes = {"scenario", "replay"}
    if args.mode not in scenario_modes and (args.scenario_file or args.manifest):
        parser.error("--scenario-file and --manifest are only valid for scenario/replay")
    if args.mode == "scenario" and args.manifest:
        parser.error("scenario mode does not accept --manifest")
    if args.mode == "replay" and args.output:
        parser.error("replay does not support --output")
    if args.mode == "scenario":
        try:
            if not args.scenario_file or not args.output:
                raise ValueError("scenario requires --scenario-file and --output")
            scenario = ScenarioDsl.loads(Path(args.scenario_file).read_text(encoding="utf-8"))
            manifest, observations = run_with_manifest(scenario, baseline.policy_id, baseline)
            if not isinstance(manifest.invariant_results, dict) or manifest.invariant_results.get("ledger") is not True:
                raise ValueError("scenario ledger invariant is missing or false")
            target = Path(args.output)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8") as stream:
                json.dump(manifest_dict(manifest), stream, sort_keys=True, indent=2)
            result = manifest_dict(manifest) | {"observations": len(observations), "output": str(target), "status": "PASS"}
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            result = {"status": "FAIL", "mode": "scenario", "error": str(exc)}
    elif args.mode == "replay":
        try:
            if not args.scenario_file or not args.manifest:
                raise ValueError("replay requires --scenario-file and --manifest")
            scenario = ScenarioDsl.loads(Path(args.scenario_file).read_text(encoding="utf-8"))
            manifest = load_manifest(args.manifest)
            if manifest.policy_id != "BASELINE_A" or manifest.config != {}:
                raise ValueError("replay supports BASELINE_A with empty config only")
            if not isinstance(manifest.invariant_results, dict) or manifest.invariant_results.get("ledger") is not True:
                raise ValueError("manifest ledger invariant is missing or false")
            result = verify_replay(manifest, scenario, baseline) | {"mode": "replay"}
        except (OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
            result = {"status": "FAIL", "mode": "replay", "error": str(exc)}
    elif args.mode == "smoke":
        scenario = synthetic_scenario(args.seed)
        manifest, observations = run_with_manifest(scenario, baseline.policy_id, baseline, mode="smoke")
        valid = isinstance(manifest.invariant_results, dict) and manifest.invariant_results.get("ledger") is True
        result = manifest_dict(manifest) | {"observations": len(observations), "status": "PASS" if valid else "FAIL"}
    elif args.mode == "build-rfp-review-queue":
        required = (args.candidates, args.queue_id, args.assembled_by, args.assembled_at, args.output)
        if not all(required):
            parser.error("build-rfp-review-queue requires --candidates, --queue-id, --assembled-by, "
                         "--assembled-at, and --output")
        queue = build_rfp_candidate_queue(
            args.candidates, queue_id=args.queue_id, assembled_by=args.assembled_by,
            assembled_at=datetime.fromisoformat(args.assembled_at),
        )
        write_rfp_candidate_queue(queue, args.output)
        result = {"status": "PASS", "mode": args.mode, "queue_id": queue.queue_id,
                  "candidate_count": queue.candidate_count, "queue_hash": queue.queue_hash,
                  "output": args.output}
    elif args.mode == "capture-rfp-candidate":
        required = (args.candidate_id, args.source_url, args.excerpt_file, args.source_quote, args.buyer,
                    args.scope, args.published_at, args.retrieved_at, args.captured_by, args.output)
        if not all(required):
            parser.error("capture-rfp-candidate requires --candidate-id, --source-url, --excerpt-file, "
                         "--source-quote, --buyer, --scope, --published-at, --retrieved-at, --captured-by, and --output")
        candidate = candidate_from_excerpt(
            excerpt=Path(args.excerpt_file).read_text(encoding="utf-8"), candidate_id=args.candidate_id,
            source_url=args.source_url, source_quote=args.source_quote, buyer=args.buyer, scope=args.scope,
            published_at=datetime.fromisoformat(args.published_at), retrieved_at=datetime.fromisoformat(args.retrieved_at),
            captured_by=args.captured_by, required_kw=args.required_kw, fuel=args.fuel,
            solicitation_number=args.solicitation_number,
            closes_at=datetime.fromisoformat(args.closes_at) if args.closes_at else None,
        )
        write_rfp_candidate(candidate, args.output)
        result = {"status": "PASS", "mode": args.mode, "candidate_id": candidate.candidate_id,
                  "candidate_hash": candidate.candidate_hash, "source_sha256": candidate.source_sha256,
                  "output": args.output}
    elif args.mode == "accept-rfp-candidate":
        required = (args.candidate, args.excerpt_file, args.fixture_id, args.reviewed_by,
                    args.verification_notes, args.opportunity_status, args.output)
        if not all(required):
            parser.error("accept-rfp-candidate requires --candidate, --excerpt-file, --fixture-id, --reviewed-by, "
                         "--verification-notes, --opportunity-status, and --output")
        bundle = accept_rfp_candidate(
            load_rfp_candidate(args.candidate), excerpt=Path(args.excerpt_file).read_text(encoding="utf-8"),
            fixture_id=args.fixture_id, reviewed_by=args.reviewed_by,
            verification_notes=args.verification_notes, opportunity_status=args.opportunity_status,
        )
        write_accepted_rfp_bundle(bundle, args.output)
        fixture = bundle.fixtures[0]
        result = {"status": "PASS", "mode": args.mode, "fixture_id": fixture.fixture_id,
                  "candidate_hash": fixture.scenario.evidence[0].claims["rfp_candidate_hash"],
                  "opportunity_status": fixture.opportunity_status,
                  "screen": screen_aura_rental_candidate(fixture.scenario.evidence).as_dict(),
                  "shortlisted": bool(current_target_fixtures(bundle)), "output": args.output}
    elif args.mode == "evaluate-retrospective":
        if not args.cohort_backtest or not args.outcome_cohort or not args.output:
            parser.error("evaluate-retrospective requires --cohort-backtest, --outcome-cohort, and --output")
        evaluation = evaluate_retrospective(load_cohort_backtest(args.cohort_backtest),
                                            load_outcome_cohort(args.outcome_cohort))
        write_retrospective_evaluation(evaluation, args.output)
        result = {"status": "PASS", "mode": "evaluate-retrospective",
                  "evaluation_hash": evaluation.evaluation_hash,
                  "evaluated_count": evaluation.evaluated_count,
                  "precision": evaluation.precision, "recall": evaluation.recall,
                  "false_alarm_rate": evaluation.false_alarm_rate, "output": args.output}
    elif args.mode == "seal-trace-outcome":
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
        failures = int(not world.ledger.verify())
        result = {"status": "FAIL" if failures else "PASS", "attacks": 1, "invariant_failures": failures,
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
