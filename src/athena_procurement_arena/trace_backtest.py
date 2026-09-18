"""Deterministic lead-time measurement over reviewed project traces."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from athena_arena.contracts import canonical_hash

from .signal_ledger import ProjectTrace, SignalType, load_trace
from .trace_cohort import load_trace_cohort


@dataclass(frozen=True)
class TraceBacktest:
    target_signal_type: SignalType
    early_signal_types: tuple[SignalType, ...]
    traces: int
    target_cases: int
    matched_cases: int
    unresolved_without_target: int
    unresolved_without_early_signal: int
    lead_seconds: tuple[int, ...]
    cases: tuple[dict[str, object], ...]

    @property
    def coverage(self) -> float:
        return round(self.matched_cases / self.target_cases, 6) if self.target_cases else 0.0

    @property
    def median_lead_seconds(self) -> int | None:
        if not self.lead_seconds:
            return None
        ordered = sorted(self.lead_seconds)
        return ordered[(len(ordered) - 1) // 2]

    @property
    def report_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "trailforge-trace-backtest-v1",
            "target_signal_type": self.target_signal_type,
            "early_signal_types": list(self.early_signal_types),
            "traces": self.traces,
            "target_cases": self.target_cases,
            "matched_cases": self.matched_cases,
            "coverage": self.coverage,
            "unresolved_without_target": self.unresolved_without_target,
            "unresolved_without_early_signal": self.unresolved_without_early_signal,
            "lead_seconds": list(self.lead_seconds),
            "median_lead_seconds": self.median_lead_seconds,
            "cases": list(self.cases),
            "report_hash": self.report_hash,
        }


@dataclass(frozen=True)
class CohortTraceBacktest:
    cohort_id: str
    cohort_hash: str
    report: TraceBacktest

    @property
    def report_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "trailforge-cohort-trace-backtest-v1",
            "cohort_id": self.cohort_id,
            "cohort_hash": self.cohort_hash,
            "report": self.report.as_dict(),
            "report_hash": self.report_hash,
        }


def backtest_traces(traces: tuple[ProjectTrace, ...] | list[ProjectTrace], *,
                    target_signal_type: SignalType,
                    early_signal_types: tuple[SignalType, ...]) -> TraceBacktest:
    """Measure only observed early-to-target pairs; absence remains unresolved."""
    if not early_signal_types:
        raise ValueError("at least one early signal type is required")
    cases: list[dict[str, object]] = []
    lead_seconds: list[int] = []
    target_cases = 0
    matched_cases = 0
    unresolved_without_target = 0
    unresolved_without_early_signal = 0
    for trace in sorted(traces, key=lambda item: item.project_id):
        targets = [item for item in trace.signals if item.signal_type == target_signal_type]
        if not targets:
            unresolved_without_target += 1
            candidates = [item for item in trace.signals if item.signal_type in early_signal_types]
            earliest = min(candidates, key=lambda item: (item.observed_at, item.signal_id)) if candidates else None
            cases.append({
                "project_id": trace.project_id,
                "trace_hash": trace.trace_hash,
                "target_signal_id": None,
                "target_observed": False,
                "earliest_signal_id": earliest.signal_id if earliest else None,
                "earliest_signal_observed_at": earliest.observed_at.isoformat() if earliest else None,
                "alerted": earliest is not None,
                "matched": False,
                "lead_seconds": None,
            })
            continue
        target = min(targets, key=lambda item: (item.observed_at, item.signal_id))
        target_cases += 1
        candidates = [item for item in trace.signals
                      if item.signal_type in early_signal_types and item.observed_at < target.observed_at]
        if not candidates:
            unresolved_without_early_signal += 1
            cases.append({"project_id": trace.project_id, "trace_hash": trace.trace_hash,
                          "target_signal_id": target.signal_id, "target_observed": True,
                          "earliest_signal_id": None, "earliest_signal_observed_at": None,
                          "alerted": False, "matched": False,
                          "lead_seconds": None})
            continue
        earliest = min(candidates, key=lambda item: (item.observed_at, item.signal_id))
        lead = int((target.observed_at - earliest.observed_at) / timedelta(seconds=1))
        matched_cases += 1
        lead_seconds.append(lead)
        cases.append({"project_id": trace.project_id, "trace_hash": trace.trace_hash,
                      "target_signal_id": target.signal_id, "target_observed": True,
                      "earliest_signal_id": earliest.signal_id,
                      "earliest_signal_observed_at": earliest.observed_at.isoformat(),
                      "alerted": True, "matched": True,
                      "lead_seconds": lead})
    return TraceBacktest(target_signal_type, tuple(early_signal_types), len(traces), target_cases,
                         matched_cases, unresolved_without_target, unresolved_without_early_signal,
                         tuple(sorted(lead_seconds)), tuple(cases))


def backtest_cohort(path: str | Path, *, target_signal_type: SignalType,
                    early_signal_types: tuple[SignalType, ...]) -> CohortTraceBacktest:
    manifest, traces = load_trace_cohort(path)
    report = backtest_traces(traces, target_signal_type=target_signal_type,
                             early_signal_types=early_signal_types)
    return CohortTraceBacktest(manifest.cohort_id, manifest.cohort_hash, report)


def _trace_backtest_from_dict(raw: dict[str, object]) -> TraceBacktest:
    if raw.get("schema_version") != "trailforge-trace-backtest-v1":
        raise ValueError("unsupported trace backtest schema_version")
    report = TraceBacktest(
        SignalType(str(raw["target_signal_type"])),
        tuple(SignalType(str(item)) for item in raw["early_signal_types"]),
        int(raw["traces"]), int(raw["target_cases"]), int(raw["matched_cases"]),
        int(raw["unresolved_without_target"]), int(raw["unresolved_without_early_signal"]),
        tuple(int(item) for item in raw["lead_seconds"]),
        tuple(dict(item) for item in raw["cases"]),
    )
    if raw.get("report_hash") != report.report_hash:
        raise ValueError("trace backtest report hash mismatch")
    return report


def load_cohort_backtest(path: str | Path) -> CohortTraceBacktest:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema_version") != "trailforge-cohort-trace-backtest-v1":
        raise ValueError("unsupported cohort trace backtest schema_version")
    report = CohortTraceBacktest(str(raw["cohort_id"]), str(raw["cohort_hash"]),
                                 _trace_backtest_from_dict(dict(raw["report"])))
    if raw.get("report_hash") != report.report_hash:
        raise ValueError("cohort trace backtest hash mismatch")
    return report


def load_traces(paths: tuple[str, ...] | list[str]) -> tuple[ProjectTrace, ...]:
    if not paths:
        raise ValueError("at least one trace path is required")
    return tuple(load_trace(path) for path in paths)


def write_backtest(report: TraceBacktest, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"backtest output already exists: {destination}")
    destination.write_text(json.dumps(report.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_cohort_backtest(report: CohortTraceBacktest, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"backtest output already exists: {destination}")
    destination.write_text(json.dumps(report.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
