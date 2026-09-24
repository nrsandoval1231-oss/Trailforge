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
                              base.timeline[0], base.timeline[0], {"extension": True},
                              tenant_id=base.tenant_id)
    extended = replace(base, evidence=base.evidence + (extension,),
                       truth=GroundTruth(base.truth.procurement_episode_id, "EXTENDED", base.truth.solicitation_at))
    return base, extended


def counterfactual_sensitivity(base: Scenario, policy_id: str, policy: Any) -> dict[str, Any]:
    left, right = paired_extension_worlds(base)
    left_world, right_world = TemporalWorld(left, policy_id, policy), TemporalWorld(right, policy_id, policy)
    left_world.run()
    right_world.run()
    left_result = _material_result(left_world)
    right_result = _material_result(right_world)
    changed = left_result != right_result
    return {"changed": changed, "observed_material_change": changed,
            "left_material": left_result, "right_material": right_result,
            "left_hash": left_world.replay_hash(), "right_hash": right_world.replay_hash()}


def _material_result(world: TemporalWorld) -> dict[str, Any]:
    """Return policy answers, excluding provenance and descriptive pattern details."""
    decision = world.ledger.records[-1]
    procurement = decision.forecast.get("procurement", {})
    power = decision.forecast.get("power", {})
    return {
        "procurement_state": procurement.get("state"),
        "procurement_confidence": procurement.get("confidence"),
        "power_status": power.get("status"),
        "power_gap_mw": power.get("peak_gap_mw"),
        "action": decision.action,
    }


def counterfactual_fact_sensitivity(base: Scenario, policy_id: str, policy: Any,
                                    fact_name: str, fact_value: Any, outcome: str,
                                    *, expected_change: bool) -> dict[str, Any]:
    fact = EvidenceEvent(f"cf-{fact_name}", "counterfactual", base.timeline[0], base.timeline[0],
                         base.timeline[0], base.timeline[0], {fact_name: fact_value},
                         tenant_id=base.tenant_id)
    altered = replace(base, evidence=base.evidence + (fact,),
                      truth=GroundTruth(base.truth.procurement_episode_id, outcome, base.truth.solicitation_at))
    left = TemporalWorld(base, policy_id, policy)
    right = TemporalWorld(altered, policy_id, policy)
    left.run()
    right.run()
    left_material = _material_result(left)
    right_material = _material_result(right)
    changed = left_material != right_material
    passed = changed == expected_change
    return {"fact": fact_name, "expected_material_change": expected_change,
            "observed_material_change": changed, "changed": changed, "passed": passed,
            "left_material": left_material, "right_material": right_material,
            "left_hash": left.replay_hash(), "right_hash": right.replay_hash()}


def counterfactual_suite(base: Scenario, policy_id: str, policy: Any) -> tuple[dict[str, Any], ...]:
    # Extension, cancellation, and private sourcing should change the answer.
    # Duplicate and unknown supply evidence should not inflate confidence or action.
    cases = (("contract_extension", True, "EXTENDED", True),
             ("duplicate_procurement", True, "DUPLICATE", False),
             ("unknown_supply", True, "UNKNOWN", False),
             ("cancellation", True, "CANCELLED", True),
             ("private_procurement", True, "PRIVATE_PROCUREMENT", True))
    return tuple(counterfactual_fact_sensitivity(base, policy_id, policy, name, value, outcome,
                                                 expected_change=expected)
                 for name, value, outcome, expected in cases)


def adversarial_recurrence_world(seed: int = 1) -> Scenario:
    """A recurrence-looking world made only of amendments, not procurements."""
    start = Scenario("adversarial-recurrence", "1", seed, (), (), GroundTruth("none", "CLOSED"))
    from datetime import datetime
    t = datetime(2026, 1, 1, tzinfo=UTC)
    events = tuple(EvidenceEvent(f"amendment-{i}", "contract", t, t, t, t,
                                 {"amendment": i, "buyer": "same"}) for i in range(3))
    return replace(start, timeline=(t,), evidence=events)
