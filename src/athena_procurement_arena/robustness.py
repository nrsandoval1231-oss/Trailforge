"""Bounded adversarial and counterfactual replay helpers."""
from __future__ import annotations

from dataclasses import replace
from datetime import UTC
from typing import Any

from .foundation import EvidenceEvent, GroundTruth, Scenario
from .world import TemporalWorld


def paired_extension_worlds(base: Scenario) -> tuple[Scenario, Scenario]:
    """Create a minimally different extension/no-extension pair."""
    extension = EvidenceEvent("extension", "contract", base.timeline[0], base.timeline[0],
                              base.timeline[0], base.timeline[0], {"contract": "extended"},
                              tenant_id=base.tenant_id)
    extended = replace(base, evidence=base.evidence + (extension,),
                       truth=GroundTruth(base.truth.procurement_episode_id, "EXTENDED", base.truth.solicitation_at))
    return base, extended


def counterfactual_sensitivity(base: Scenario, policy_id: str, policy: Any) -> dict[str, Any]:
    left, right = paired_extension_worlds(base)
    left_world, right_world = TemporalWorld(left, policy_id, policy), TemporalWorld(right, policy_id, policy)
    left_world.run()
    right_world.run()
    left_actions = tuple(item.action for item in left_world.ledger.records)
    right_actions = tuple(item.action for item in right_world.ledger.records)
    changed = left_actions != right_actions or left_world.replay_hash() != right_world.replay_hash()
    return {"changed": changed, "left_hash": left_world.replay_hash(), "right_hash": right_world.replay_hash()}


def counterfactual_fact_sensitivity(base: Scenario, policy_id: str, policy: Any,
                                    fact_name: str, fact_value: Any, outcome: str) -> dict[str, Any]:
    fact = EvidenceEvent(f"cf-{fact_name}", "counterfactual", base.timeline[0], base.timeline[0],
                         base.timeline[0], base.timeline[0], {fact_name: fact_value},
                         tenant_id=base.tenant_id)
    altered = replace(base, evidence=base.evidence + (fact,),
                      truth=GroundTruth(base.truth.procurement_episode_id, outcome, base.truth.solicitation_at))
    left = TemporalWorld(base, policy_id, policy)
    right = TemporalWorld(altered, policy_id, policy)
    left.run()
    right.run()
    return {"fact": fact_name, "changed": left.replay_hash() != right.replay_hash(),
            "left_hash": left.replay_hash(), "right_hash": right.replay_hash()}


def counterfactual_suite(base: Scenario, policy_id: str, policy: Any) -> tuple[dict[str, Any], ...]:
    cases = (("contract_extension", True, "EXTENDED"), ("duplicate_procurement", True, "DUPLICATE"),
             ("unknown_supply", True, "UNKNOWN"), ("cancellation", True, "CANCELLED"),
             ("private_procurement", True, "PRIVATE_PROCUREMENT"))
    return tuple(counterfactual_fact_sensitivity(base, policy_id, policy, name, value, outcome)
                 for name, value, outcome in cases)


def adversarial_recurrence_world(seed: int = 1) -> Scenario:
    """A recurrence-looking world made only of amendments, not procurements."""
    start = Scenario("adversarial-recurrence", "1", seed, (), (), GroundTruth("none", "CLOSED"))
    from datetime import datetime
    t = datetime(2026, 1, 1, tzinfo=UTC)
    events = tuple(EvidenceEvent(f"amendment-{i}", "contract", t, t, t, t,
                                 {"amendment": i, "buyer": "same"}) for i in range(3))
    return replace(start, timeline=(t,), evidence=events)
