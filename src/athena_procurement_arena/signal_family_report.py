"""Cohort comparison of candidate signal families by lead time, coverage and action burden."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from athena_arena.contracts import canonical_hash

from .signal_ledger import ProjectTrace, SignalType
from .trace_cohort import load_trace_cohort

MIN_COHORT = 20
MAX_COHORT = 50
MIN_MATCHED_FOR_USEFUL = 5


@dataclass(frozen=True)
class SignalFamilyResult:
    signal_type: SignalType
    target_cases: int
    surfaced_cases: int
    matched_cases: int
    false_surfaces: int
    signals_per_surfaced_project: float | None
    buyer_path_cases: int
    lead_days: tuple[float, ...]

    @property
    def coverage(self) -> float:
        return round(self.matched_cases / self.target_cases, 6) if self.target_cases else 0.0

    @property
    def median_lead_days(self) -> float | None:
        if not self.lead_days:
            return None
        ordered = sorted(self.lead_days)
        return ordered[(len(ordered) - 1) // 2]

    @property
    def buyer_path_rate(self) -> float | None:
        return round(self.buyer_path_cases / self.matched_cases, 6) if self.matched_cases else None

    @property
    def repeatable(self) -> bool:
        """Positive median lead on enough matched projects; a screen, not proof of commercial value."""
        median = self.median_lead_days
        return self.matched_cases >= MIN_MATCHED_FOR_USEFUL and median is not None and median > 0

    def as_dict(self) -> dict[str, object]:
        return {
            "signal_type": self.signal_type, "target_cases": self.target_cases,
            "surfaced_cases": self.surfaced_cases, "matched_cases": self.matched_cases,
            "coverage": self.coverage, "median_lead_days": self.median_lead_days,
            "false_surfaces": self.false_surfaces,
            "signals_per_surfaced_project": self.signals_per_surfaced_project,
            "buyer_path_cases": self.buyer_path_cases, "buyer_path_rate": self.buyer_path_rate,
            "repeatable": self.repeatable, "lead_days": list(self.lead_days),
        }


@dataclass(frozen=True)
class SignalFamilyReport:
    cohort_id: str
    cohort_hash: str
    target_signal_type: SignalType
    projects: int
    projects_with_target: int
    families: tuple[SignalFamilyResult, ...]

    @property
    def cohort_status(self) -> str:
        if self.projects < MIN_COHORT:
            return f"BELOW_TARGET: {self.projects} projects, need {MIN_COHORT}-{MAX_COHORT}"
        if self.projects > MAX_COHORT:
            return f"ABOVE_TARGET: {self.projects} projects, scope is {MIN_COHORT}-{MAX_COHORT}"
        return "IN_TARGET_RANGE"

    @property
    def report_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "trailforge-signal-family-report-v1",
            "cohort_id": self.cohort_id, "cohort_hash": self.cohort_hash,
            "target_signal_type": self.target_signal_type, "projects": self.projects,
            "projects_with_target": self.projects_with_target, "cohort_status": self.cohort_status,
            "any_family_repeatable": any(item.repeatable for item in self.families),
            "families": [item.as_dict() for item in self.families],
            "report_hash": self.report_hash,
        }


def _has_buyer_path(trace: ProjectTrace, surface_at) -> bool:
    return any(item.claims.get("buyer_path") for item in trace.signals if item.observed_at <= surface_at)


def _family(traces: tuple[ProjectTrace, ...], family: SignalType, target: SignalType) -> SignalFamilyResult:
    target_cases = surfaced = matched = false_surfaces = buyer_cases = 0
    family_signal_counts: list[int] = []
    leads: list[float] = []
    for trace in traces:
        targets = [item for item in trace.signals if item.signal_type == target]
        target_at = min(item.observed_at for item in targets) if targets else None
        if target_at:
            target_cases += 1
        pool = [item for item in trace.signals if item.signal_type == family]
        pool = [item for item in pool if target_at is None or item.observed_at < target_at]
        if not pool:
            continue
        surfaced += 1
        family_signal_counts.append(len(pool))
        if target_at is None:
            false_surfaces += 1
            continue
        first = min(item.observed_at for item in pool)
        matched += 1
        leads.append(round((target_at - first) / timedelta(days=1), 3))
        if _has_buyer_path(trace, first):
            buyer_cases += 1
    burden = round(sum(family_signal_counts) / surfaced, 3) if surfaced else None
    return SignalFamilyResult(family, target_cases, surfaced, matched, false_surfaces, burden,
                              buyer_cases, tuple(sorted(leads)))


def compare_signal_families(traces: tuple[ProjectTrace, ...] | list[ProjectTrace], *,
                            target_signal_type: SignalType, cohort_id: str = "adhoc",
                            cohort_hash: str = "") -> SignalFamilyReport:
    """Treat each non-target signal type as a one-family policy and measure it independently."""
    ordered = tuple(sorted(traces, key=lambda item: item.project_id))
    seen = {item.signal_type for trace in ordered for item in trace.signals} - {target_signal_type}
    families = tuple(_family(ordered, family, target_signal_type) for family in sorted(seen))
    with_target = sum(any(item.signal_type == target_signal_type for item in trace.signals) for trace in ordered)
    return SignalFamilyReport(cohort_id, cohort_hash, target_signal_type, len(ordered), with_target, families)


def compare_cohort_signal_families(path: str | Path, *, target_signal_type: SignalType) -> SignalFamilyReport:
    manifest, traces = load_trace_cohort(path)
    return compare_signal_families(traces, target_signal_type=target_signal_type,
                                   cohort_id=manifest.cohort_id, cohort_hash=manifest.cohort_hash)


def write_signal_family_report(report: SignalFamilyReport, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"signal family report output already exists: {destination}")
    destination.write_text(json.dumps(report.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
