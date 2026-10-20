"""Small deterministic synthetic campaign runner for mechanics benchmarking."""
from __future__ import annotations

import time
import tracemalloc
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from .foundation import EvidenceEvent, GroundTruth, Scenario
from .world import TemporalWorld


def synthetic_scenario(seed: int) -> Scenario:
    t = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=seed % 28)
    kind = seed % 4
    claims = ({"capital": "funded"} if kind == 0 else {"permit": "issued"} if kind == 1
              else {"engineering": "active"} if kind == 2 else {"rfp": "released"})
    tenant_id = f"tenant-{seed % 3}"
    event = EvidenceEvent(f"p-{seed}", f"source-{kind}", t, t, t, t, claims, tenant_id=tenant_id)
    return Scenario(f"synthetic-{seed}", "1", seed, (t,), (event,),
                    GroundTruth(f"p-{seed}", "OPEN"), tenant_id=tenant_id)


def run_campaign(count: int, policies: dict[str, Callable[[Any], tuple[dict[str, Any], str]]], seed: int = 1,
                 trace_memory: bool = False) -> dict[str, Any]:
    if count < 1:
        raise ValueError("campaign count must be positive")
    # tracemalloc taxes every allocation (~5x slower), so it is opt-in and never mixed into throughput claims.
    owns_tracer = trace_memory and not tracemalloc.is_tracing()
    if owns_tracer:
        tracemalloc.start()
    elif trace_memory:
        tracemalloc.reset_peak()
    peak_memory_bytes = None
    try:
        started = time.perf_counter()
        world_seconds = 0.0
        totals = {name: {"runs": 0, "actionable": 0, "invariant_failures": 0} for name in policies}
        for offset in range(count):
            scenario = synthetic_scenario(seed + offset)
            for name, policy in policies.items():
                world = TemporalWorld(scenario, name, policy)
                world_started = time.perf_counter()
                world.run()
                world_seconds += time.perf_counter() - world_started
                totals[name]["runs"] += 1
                totals[name]["actionable"] += sum(
                    record.action in {"RESEARCH", "PREPARE", "BID_REVIEW"} for record in world.ledger.records)
                totals[name]["invariant_failures"] += int(not world.ledger.verify())
        elapsed = time.perf_counter() - started
        if trace_memory:
            _, peak_memory_bytes = tracemalloc.get_traced_memory()
    finally:
        if owns_tracer:
            tracemalloc.stop()
    executed_runs = count * len(policies)
    failures = sum(item["invariant_failures"] for item in totals.values())
    return {"status": "FAIL" if failures else "PASS", "count": count, "seed": seed, "policies": totals,
            "elapsed_seconds": round(elapsed, 6), "runs_per_second": round(count / elapsed, 2),
            "observability": {
                "executed_policy_runs": executed_runs,
                "average_policy_latency_ms": round((world_seconds / executed_runs) * 1000, 4),
                "policy_runner_seconds": round(world_seconds, 6),
                "peak_memory_bytes": peak_memory_bytes,
                "storage_bytes": 0,
                "athena_model_calls": 0,
                "estimated_cost": 0.0,
                "failures": failures,
            }}


def run_family_campaign(policies: dict[str, Callable[[Any], tuple[dict[str, Any], str]]], seed: int = 1) -> dict[str, Any]:
    from .scenarios import SCENARIO_FAMILIES, family_scenario
    totals = {name: {"runs": 0, "invariant_failures": 0} for name in policies}
    for index, family in enumerate(SCENARIO_FAMILIES):
        scenario = family_scenario(family, seed + index)
        for name, policy in policies.items():
            world = TemporalWorld(scenario, name, policy)
            world.run()
            totals[name]["runs"] += 1
            totals[name]["invariant_failures"] += int(not world.ledger.verify())
    failures = sum(item["invariant_failures"] for item in totals.values())
    return {"status": "FAIL" if failures else "PASS", "family_count": len(SCENARIO_FAMILIES), "seed": seed, "policies": totals}


def run_regression_campaign(policies: dict[str, Callable[[Any], tuple[dict[str, Any], str]]], seed: int = 1) -> dict[str, Any]:
    """Evaluate every family and return separate aggregate metrics per policy."""
    from .evaluation import evaluate_replay
    from .scenarios import SCENARIO_FAMILIES, family_scenario
    results = {}
    for name, policy in policies.items():
        rows = []
        invariant_failures = 0
        for index, family in enumerate(SCENARIO_FAMILIES):
            scenario = family_scenario(family, seed + index)
            world = TemporalWorld(scenario, name, policy)
            world.run()
            result = evaluate_replay(scenario, world.ledger.records)
            invariant_failures += int(not world.ledger.verify())
            rows.append(result)
        recalls = [row.discovery["recall"] for row in rows]
        precisions = [row.discovery["precision"] for row in rows if row.discovery["precision"] is not None]
        rows_with_power = [row for row in rows if row.power["status"] != "UNAVAILABLE"]
        results[name] = {"runs": len(rows), "invariant_failures": invariant_failures,
                         "discovery_recall": sum(recalls) / len(recalls),
                         "discovery_precision": sum(precisions) / len(precisions) if precisions else None,
                         "power_evaluated_runs": len(rows_with_power),
                         "actionable_steps": sum(row.action["actionable_steps"] for row in rows)}
    failures = sum(item["invariant_failures"] for item in results.values())
    return {"status": "FAIL" if failures else "PASS", "family_count": len(SCENARIO_FAMILIES), "seed": seed, "policies": results}


def run_mutation_campaign(base: Scenario, count: int, policies: dict[str, Callable[[Any], tuple[dict[str, Any], str]]], seed: int = 1) -> dict[str, Any]:
    from .mutations import mutate_scenarios
    variants = mutate_scenarios(base, count, seed=seed)
    totals = {name: {"runs": 0, "invariant_failures": 0} for name in policies}
    for scenario, _ in variants:
        for name, policy in policies.items():
            world = TemporalWorld(scenario, name, policy)
            world.run()
            totals[name]["runs"] += 1
            totals[name]["invariant_failures"] += int(not world.ledger.verify())
    failures = sum(item["invariant_failures"] for item in totals.values())
    return {"status": "FAIL" if failures else "PASS", "variant_count": count, "seed": seed, "policies": totals}
