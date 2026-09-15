"""Seeded, truth-preserving scenario mutations."""
from __future__ import annotations

import random
from dataclasses import dataclass, replace
from datetime import timedelta

from .foundation import Scenario, validate_scenario

MUTATION_OPERATIONS = (
    "availability_delay",
    "lineage_version",
    "procurement_route",
    "funding_status",
    "utility_supply",
    "power_requirement",
    "source_authority",
    "duplicate_lineage",
    "identity_ambiguity",
    "buyer_history",
    "schedule_compression",
    "contradiction",
)


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
        operation = MUTATION_OPERATIONS[index % len(MUTATION_OPERATIONS)]
        if operation == "availability_delay":
            evidence = tuple(replace(item, verified_available_at=item.verified_available_at + timedelta(days=delay),
                                     observed_at=item.observed_at + timedelta(days=delay)) for item in base.evidence)
            parameters = {"delay_days": delay}
        elif operation == "lineage_version":
            evidence = tuple(replace(item, source_version=f"mut-{index}") for item in base.evidence)
            parameters = {"source_version": f"mut-{index}"}
        else:
            def update(item, *, operation=operation, index=index, delay=delay):
                claims = dict(item.claims)
                kwargs = {}
                if operation == "procurement_route":
                    claims["procurement_route"] = ("PUBLIC_RFP", "PRIVATE_RFQ", "DIRECT")[index % 3]
                elif operation == "funding_status":
                    claims["funding"] = ("FUNDED", "DEFERRED", "DENIED")[index % 3]
                elif operation == "utility_supply":
                    claims["supply_mw"] = (None, 0.5, 2.0)[index % 3]
                elif operation == "power_requirement":
                    claims["required_mw"] = (0.25, 1.0, 5.0)[index % 3]
                elif operation == "source_authority":
                    kwargs["authority"] = ("PRIMARY", "SECONDARY", "UNKNOWN")[index % 3]
                elif operation == "duplicate_lineage":
                    kwargs["lineage_family"] = f"syndication-{index % 4}"
                elif operation == "identity_ambiguity":
                    kwargs["entity_candidates"] = (f"project-{index % 3}", f"project-alt-{index % 3}")
                elif operation == "buyer_history":
                    claims["buyer"] = f"buyer-{index % 5}"
                elif operation == "schedule_compression":
                    claims["deadline_compression_days"] = delay
                elif operation == "contradiction":
                    kwargs["contradictions"] = (f"contradiction-{index}",)
                return replace(item, claims=claims, **kwargs)

            evidence = tuple(update(item) for item in base.evidence)
            parameters = {"variant_index": index}
        scenario = replace(base, scenario_id=f"{base.scenario_id}-m{index}", evidence=evidence)
        validate_scenario(scenario)
        record = MutationRecord(f"{base.scenario_id}-mutation-{index}", base.scenario_id,
                                base.seed if seed is None else seed, operation, parameters)
        variants.append((scenario, record))
    return tuple(variants)
