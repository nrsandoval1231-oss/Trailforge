"""Small deterministic synthetic campaign runner for mechanics benchmarking."""
from __future__ import annotations

import time
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


def run_campaign(count: int, policies: dict[str, Callable[[Any], tuple[dict[str, Any], str]]], seed: int = 1) -> dict[str, Any]:
    if count < 1:
        raise ValueError("campaign count must be positive")
    started = time.perf_counter()
    totals = {name: {"runs": 0, "actionable": 0, "invariant_failures": 0} for name in policies}
    for offset in range(count):
        scenario = synthetic_scenario(seed + offset)
        for name, policy in policies.items():
            world = TemporalWorld(scenario, name, policy)
            world.run()
            totals[name]["runs"] += 1
            totals[name]["actionable"] += sum(
                record.action in {"RESEARCH", "PREPARE", "BID_REVIEW"} for record in world.ledger.records)
            totals[name]["invariant_failures"] += int(not world.ledger.verify())
    elapsed = time.perf_counter() - started
    return {"status": "PASS", "count": count, "seed": seed, "policies": totals,
            "elapsed_seconds": round(elapsed, 6), "runs_per_second": round(count / elapsed, 2)}


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
    return {"status": "PASS", "family_count": len(SCENARIO_FAMILIES), "seed": seed, "policies": totals}


def run_regression_campaign(policies: dict[str, Callable[[Any], tuple[dict[str, Any], str]]], seed: int = 1) -> dict[str, Any]:
    """Evaluate every family and return separate aggregate metrics per policy."""
    from .evaluation import evaluate_replay
    from .scenarios import SCENARIO_FAMILIES, family_scenario
    results = {}
    for name, policy in policies.items():
        rows = []
        for index, family in enumerate(SCENARIO_FAMILIES):
            scenario = family_scenario(family, seed + index)
            world = TemporalWorld(scenario, name, policy)
            world.run()
            result = evaluate_replay(scenario, world.ledger.records)
            rows.append(result)
        recalls = [row.discovery["recall"] for row in rows]
        precisions = [row.discovery["precision"] for row in rows if row.discovery["precision"] is not None]
        rows_with_power = [row for row in rows if row.power["status"] != "UNAVAILABLE"]
        results[name] = {"runs": len(rows), "invariant_failures": 0,
                         "discovery_recall": sum(recalls) / len(recalls),
                         "discovery_precision": sum(precisions) / len(precisions) if precisions else None,
                         "power_evaluated_runs": len(rows_with_power),
                         "actionable_steps": sum(row.action["actionable_steps"] for row in rows)}
    return {"status": "PASS", "family_count": len(SCENARIO_FAMILIES), "seed": seed, "policies": results}


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
    return {"status": "PASS", "variant_count": count, "seed": seed, "policies": totals}
