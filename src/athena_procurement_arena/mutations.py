"""Seeded, truth-preserving scenario mutations."""
from __future__ import annotations

import random
from dataclasses import dataclass, replace
from datetime import timedelta

from .foundation import EvidenceEvent, Scenario, validate_scenario


@dataclass(frozen=True)
class MutationRecord:
    mutation_id: str
    parent_scenario_id: str
    seed: int
    operation: str
    parameters: dict[str, object]


def mutate_scenarios(base: Scenario, count: int, seed: int | None = None) -> tuple[tuple[Scenario, MutationRecord], ...]:
    if count < 0:
        raise ValueError("mutation count cannot be negative")
    rng = random.Random(base.seed if seed is None else seed)
    variants = []
    for index in range(count):
        delay = rng.randint(0, 3)
        operation = "availability_delay" if index % 2 == 0 else "lineage_version"
        if operation == "availability_delay":
            evidence = tuple(replace(item, verified_available_at=item.verified_available_at + timedelta(days=delay),
                                     observed_at=item.observed_at + timedelta(days=delay)) for item in base.evidence)
        else:
            evidence = tuple(replace(item, source_version=f"mut-{index}") for item in base.evidence)
        scenario = replace(base, scenario_id=f"{base.scenario_id}-m{index}", evidence=evidence)
        validate_scenario(scenario)
        record = MutationRecord(f"{base.scenario_id}-mutation-{index}", base.scenario_id,
                                base.seed if seed is None else seed, operation, {"delay_days": delay})
        variants.append((scenario, record))
    return tuple(variants)
