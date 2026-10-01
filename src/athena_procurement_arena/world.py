"""Deterministic event-driven scenario replay."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, fields, is_dataclass, replace
from types import MappingProxyType
from typing import Any

from athena_arena.contracts import canonical_hash

from .foundation import (
    FrozenDecision,
    FrozenDecisionLedger,
    InvariantViolation,
    Scenario,
    _deep_freeze,
    validate_recommended_action,
    validate_scenario,
)


def _freeze_policy_input(value: Any) -> Any:
    if is_dataclass(value):
        return MappingProxyType({item.name: _freeze_policy_input(getattr(value, item.name))
                                 for item in fields(value)})
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_policy_input(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_policy_input(item) for item in value)
    return _deep_freeze(value)

PolicyCallback = Callable[[Any], tuple[dict[str, Any], str]]

@dataclass(frozen=True)
class WorldObservation:
    scenario_id: str
    simulation_time: Any
    visible_evidence_ids: tuple[str, ...]
    decision_hash: str

class TemporalWorld:
    """Advance only along the declared timeline and freeze every policy output."""
    def __init__(self, scenario: Scenario, policy_id: str, policy: PolicyCallback) -> None:
        self.scenario, self.policy_id, self.policy = scenario, policy_id, policy
        self.ledger = FrozenDecisionLedger()
        self.decision_snapshots: list[dict[str, Any]] = []
        self._cursor = -1
        self._scenario_hash = validate_scenario(scenario)

    @property
    def scenario_hash(self) -> str:
        return self._scenario_hash

    def step(self) -> WorldObservation:
        # Revalidate the publicly reachable scenario in case a caller replaces
        # it after construction; permission must hold at each policy boundary.
        current_scenario_hash = validate_scenario(self.scenario)
        if current_scenario_hash != self._scenario_hash:
            raise InvariantViolation("scenario hash changed after construction")
        if self._cursor + 1 >= len(self.scenario.timeline):
            raise StopIteration("scenario timeline exhausted")
        next_cursor = self._cursor + 1
        now = self.scenario.timeline[next_cursor]
        visible = tuple(sorted(e.evidence_id for e in self.scenario.evidence if e.visible_at(now)))
        visible_items = tuple(
            replace(e, action_support=None)
            if e.action_support is not None and e.action_support.reviewed_at > now else e
            for e in self.scenario.evidence if e.evidence_id in visible
        )
        state = {"scenario_id": self.scenario.scenario_id, "time": now,
                 "visible_evidence_ids": visible, "visible_evidence": visible_items,
                 "seed": self.scenario.seed}
        snapshot = _freeze_policy_input(state)
        forecast, action = self.policy(state)
        validate_recommended_action(action)
        decision = self.ledger.append(FrozenDecision(self.scenario.scenario_id, now,
            self.policy_id, visible, forecast, action))
        self.decision_snapshots.append({"decision_time": now, "policy_id": self.policy_id,
                                        "policy_input": snapshot, "policy_output": decision.forecast,
                                        "action": decision.action, "decision_hash": decision.record_hash})
        self._cursor = next_cursor
        return WorldObservation(self.scenario.scenario_id, now, visible, decision.record_hash)

    def run(self) -> tuple[WorldObservation, ...]:
        return tuple(self.step() for _ in self.scenario.timeline[self._cursor + 1:])

    def replay_hash(self) -> str:
        return canonical_hash(self.ledger.records)
