"""Run HC-001 locally without network access."""
from __future__ import annotations

import argparse
from pathlib import Path

from athena_procurement_arena.historical_cohort import build_historical_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="reviewed cohort JSON input")
    parser.add_argument("output", type=Path, help="new or empty output directory")
    args = parser.parse_args()
    report = build_historical_report(args.input, args.output)
    print(f"wrote {args.output / 'report.json'}; projects={report['project_count']} eligible_traces={report['eligible_trace_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
