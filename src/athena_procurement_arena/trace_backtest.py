"""Deterministic lead-time measurement over reviewed project traces."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from athena_arena.contracts import canonical_hash

from .signal_ledger import ProjectTrace, SignalType, load_trace


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
            continue
        target = min(targets, key=lambda item: (item.observed_at, item.signal_id))
        target_cases += 1
        candidates = [item for item in trace.signals
                      if item.signal_type in early_signal_types and item.observed_at < target.observed_at]
        if not candidates:
            unresolved_without_early_signal += 1
            cases.append({"project_id": trace.project_id, "target_signal_id": target.signal_id,
                          "matched": False})
            continue
        earliest = min(candidates, key=lambda item: (item.observed_at, item.signal_id))
        lead = int((target.observed_at - earliest.observed_at) / timedelta(seconds=1))
        matched_cases += 1
        lead_seconds.append(lead)
        cases.append({"project_id": trace.project_id, "target_signal_id": target.signal_id,
                      "earliest_signal_id": earliest.signal_id, "matched": True,
                      "lead_seconds": lead})
    return TraceBacktest(target_signal_type, tuple(early_signal_types), len(traces), target_cases,
                         matched_cases, unresolved_without_target, unresolved_without_early_signal,
                         tuple(sorted(lead_seconds)), tuple(cases))


def load_traces(paths: tuple[str, ...] | list[str]) -> tuple[ProjectTrace, ...]:
    if not paths:
        raise ValueError("at least one trace path is required")
    return tuple(load_trace(path) for path in paths)


def write_backtest(report: TraceBacktest, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"backtest output already exists: {destination}")
    destination.write_text(json.dumps(report.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
