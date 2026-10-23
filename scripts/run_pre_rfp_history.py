"""Run the fixed, offline three-family historical pre-RFP backtrace."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from athena_arena.contracts import canonical_hash

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from athena_procurement_arena.historical_case_report import build_case_report  # noqa: E402
from athena_procurement_arena.historical_cases import (  # noqa: E402
    load_case,
    replay_case,
    validate_family_splits,
)
from athena_procurement_arena.policies import BaselineA  # noqa: E402


def run(output_dir: Path) -> dict:
    cases_dir = ROOT / "research/pre-rfp-history/cases"
    paths = [cases_dir / name / "case.json" for name in ("crusoe-abilene", "montauk-2021", "azure-sky-wind")]
    loaded = [load_case(path) for path in paths]
    cases = [item[0] for item in loaded]
    validate_family_splits(cases)
    output_dir.mkdir(parents=True, exist_ok=False)
    results, reports = [], []
    burden_path = ROOT / "research/pre-rfp-history/recovery-attempts/BURDEN.json"
    burden = json.loads(burden_path.read_text(encoding="utf-8"))
    burden_by_case = {item["case_id"]: item for item in burden["cases"]}
    for path, (case, scenario) in zip(paths, loaded, strict=True):
        result = replay_case(path, mode="BACKTRACE", policy=BaselineA(),
                             experiment_dir=output_dir / "experiments" / case.case_id)
        case_burden = burden_by_case[case.case_id]
        report = build_case_report(case, scenario, result, {
            "source": "research/pre-rfp-history/recovery-attempts/BURDEN.json",
            **case_burden,
        })
        source_timeline = [{"evidence_id": ref.evidence_id, "source_url": ref.source_url,
            "source_quote": ref.source_quote,
            "reported_source_document_date": ref.extra_fields.get("reported_document_date", "UNKNOWN"),
            "reported_source_event_date": ref.extra_fields.get("reported_event_date", "UNKNOWN"),
            "source_date_precision": "DAY" if ref.extra_fields.get("reported_document_date", "UNKNOWN") != "UNKNOWN" else "UNKNOWN",
            "source_date_timezone": "UNKNOWN",
            "representation_observation_at": ref.verified_available_at,
            "source_observed_at": ref.observed_at,
            "date_semantics": ref.extra_fields.get("date_semantics", "UNKNOWN"),
            "buyer_organization": ref.reviewed_claims.get("buyer_organization", "UNKNOWN"),
            "generation_need_supported": ref.reviewed_claims.get("generation_need_supported", "UNKNOWN"),
            "replay_included": ref.replay_included} for ref in case.evidence_sources]
        report["source_timeline"] = source_timeline
        result["experiment_dir"] = f"experiments/{case.case_id}"
        results.append(result)
        reports.append(report)
    summary = {"schema_version": "trailforge-pre-rfp-history-v2", "mode": "BACKTRACE",
        "policy_id": "PRE_RFP_BASELINE_V1", "comparator_policy_id": "BASELINE_A",
        "discovery_credit": False, "cases": reports, "replays": results,
        "research_burden": burden}
    summary["cohort_hash"] = canonical_hash(summary)
    (output_dir / "cohort.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    lines = ["# Historical pre-RFP backtrace", "", "Three purposive development cases. Discovery credit: none.",
             "Buyer routes and explicit generation solicitation releases require source proof; unknowns remain unknown.", ""]
    for item in reports:
        lines.extend([f"## {item['case_id']}", "", f"First policy surface: {item['first_policy_surface_at']}",
            f"First buyer-actionable time: {item['first_buyer_actionable_at']}",
            f"Verified generation solicitation: {item['verified_generation_solicitation']}",
            f"Lead seconds: {item['historical_lead_seconds']} ({item['lead_status']})",
            f"Missing reasons: {', '.join(item['missing_reasons']) or 'none'}",
            f"Source timeline: {json.dumps(item['source_timeline'], sort_keys=True)}",
            f"Invalidators: {', '.join(item['invalidators']) or 'none recorded'}", ""])
    lines.extend(["## Research burden", "", "Public request/search counts are itemized by case from retained recovery receipts.",
                  "HTTP latency is not total research time; prior research and human review time remain UNKNOWN.", ""])
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "research/pre-rfp-history/results-v2")
    args = parser.parse_args()
    result = run(args.output_dir)
    print(json.dumps({"status": "PASS", "cases": len(result["cases"]),
                      "cohort_hash": result["cohort_hash"], "output_dir": str(args.output_dir)}, sort_keys=True))
