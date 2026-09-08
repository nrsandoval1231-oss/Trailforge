"""Bounded adversarial and counterfactual replay helpers."""
from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from typing import Any

from .foundation import EvidenceEvent, GroundTruth, Scenario
from .world import TemporalWorld


def paired_extension_worlds(base: Scenario) -> tuple[Scenario, Scenario]:
    """Create a minimally different extension/no-extension pair."""
    extension = EvidenceEvent("extension", "contract", base.timeline[0], base.timeline[0],
                              base.timeline[0], base.timeline[0], {"contract": "extended"})
    extended = replace(base, evidence=base.evidence + (extension,),
                       truth=GroundTruth(base.truth.procurement_episode_id, "EXTENDED", base.truth.solicitation_at))
    return base, extended


def counterfactual_sensitivity(base: Scenario, policy_id: str, policy: Any) -> dict[str, Any]:
    left, right = paired_extension_worlds(base)
    left_world, right_world = TemporalWorld(left, policy_id, policy), TemporalWorld(right, policy_id, policy)
    left_world.run(); right_world.run()
    left_actions = tuple(item.action for item in left_world.ledger.records)
    right_actions = tuple(item.action for item in right_world.ledger.records)
    changed = left_actions != right_actions or left_world.replay_hash() != right_world.replay_hash()
    return {"changed": changed, "left_hash": left_world.replay_hash(), "right_hash": right_world.replay_hash()}


def adversarial_recurrence_world(seed: int = 1) -> Scenario:
    """A recurrence-looking world made only of amendments, not procurements."""
    start = Scenario("adversarial-recurrence", "1", seed, (), (), GroundTruth("none", "CLOSED"))
    times = tuple(start_time + timedelta(days=i) for i, start_time in enumerate(()))
    # Construct explicitly to avoid hidden wall-clock state.
    from datetime import datetime, timezone
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    events = tuple(EvidenceEvent(f"amendment-{i}", "contract", t, t, t, t,
                                 {"amendment": i, "buyer": "same"}) for i in range(3))
    return replace(start, timeline=(t,), evidence=events)
