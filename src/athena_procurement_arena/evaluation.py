"""Component metrics for deterministic policy replay."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .foundation import FrozenDecision, Scenario


@dataclass(frozen=True)
class EvaluationResult:
    discovery: dict[str, float | int | None]
    trail: dict[str, float | int | None]
    procurement: dict[str, float | int | None]
    power: dict[str, float | int | None]
    action: dict[str, float | int | None]
    efficiency: dict[str, float | int | None]
    invariant_status: str = "PASS"

    def as_dict(self) -> dict[str, Any]:
        return {"discovery": self.discovery, "trail": self.trail, "procurement": self.procurement,
                "power": self.power, "action": self.action, "efficiency": self.efficiency,
                "invariant_status": self.invariant_status}


def evaluate_replay(scenario: Scenario, decisions: tuple[FrozenDecision, ...]) -> EvaluationResult:
    """Evaluate independently observable dimensions; unavailable truth stays unavailable."""
    visible = set().union(*(set(item.visible_evidence_ids) for item in decisions)) if decisions else set()
    expected = scenario.truth.procurement_episode_id
    recognized = any(expected in item.visible_evidence_ids for item in decisions)
    precision = 1.0 if recognized and visible else (0.0 if visible else None)
    recall = 1.0 if recognized else 0.0
    predicted_states = [item.forecast.get("procurement", {}).get("state") for item in decisions]
    next_event_known = scenario.truth.outcome in predicted_states
    actionable = sum(item.action in {"RESEARCH", "PREPARE", "BID_REVIEW"} for item in decisions)
    useful_lead = None
    if scenario.truth.solicitation_at and recognized:
        first = next(item.simulation_time for item in decisions if expected in item.visible_evidence_ids)
        useful_lead = max(0.0, (scenario.truth.solicitation_at - first).total_seconds())
    return EvaluationResult(
        discovery={"precision": precision, "recall": recall, "visible_evidence": len(visible)},
        trail={"episode_resolved": int(recognized), "entity_linkage": None},
        procurement={"next_event_correct": int(next_event_known), "useful_lead_seconds": useful_lead},
        power={"numeric_error_mw": None, "status": "UNAVAILABLE"},
        action={"actionable_steps": actionable, "attention_burden": len(decisions)},
        efficiency={"decision_count": len(decisions)},
    )
