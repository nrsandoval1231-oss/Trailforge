"""Component metrics for deterministic policy replay."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any

from athena_arena.contracts import canonical_hash

from .foundation import FrozenDecision, Scenario


def _verify_decisions(decisions: tuple[FrozenDecision, ...]) -> bool | None:
    """Verify supplied decision hashes; missing decisions have no basis."""
    if not decisions:
        return None
    previous = ""
    for decision in decisions:
        if decision.previous_hash != previous:
            return False
        payload = {item.name: getattr(decision, item.name) for item in fields(decision)
                   if item.name != "record_hash"}
        if decision.record_hash != canonical_hash(payload):
            return False
        previous = decision.record_hash
    return True


def evaluate_power_profile(profile: tuple[dict[str, Any], ...], expected_peak_gap_mw: float | None) -> dict[str, Any]:
    """Evaluate peak gap only when a verified numeric truth value is supplied."""
    if expected_peak_gap_mw is None:
        return {"status": "UNAVAILABLE", "peak_gap_error_mw": None}
    known = [item["gap_mw"] for item in profile if item.get("gap_mw") is not None]
    if not known:
        return {"status": "UNKNOWN", "peak_gap_error_mw": None}
    if any(item.get("gap_mw") is None for item in profile):
        return {"status": "UNKNOWN", "peak_gap_error_mw": None}
    actual = max(known)
    return {"status": "PASS", "peak_gap_mw": actual,
            "peak_gap_error_mw": abs(actual - expected_peak_gap_mw)}


def attention_metrics(ranked_trail_ids: tuple[str, ...], relevant_ids: frozenset[str], ks=(5, 10, 25, 50)) -> dict[str, dict[str, float]]:
    """Return Precision@K/Recall@K without rewarding duplicate or excess alerts."""
    result = {}
    for k in ks:
        selected = ranked_trail_ids[:k]
        hits = len(set(selected) & relevant_ids)
        result[str(k)] = {"precision": hits / len(selected) if selected else 0.0,
                          "recall": hits / len(relevant_ids) if relevant_ids else 0.0}
    return result


def useful_lead_time_seconds(procurement_time, first_detection, *, actionable: bool) -> float | None:
    """Credit lead time only when the first detection supports a real action."""
    if not actionable:
        return None
    return max(0.0, (procurement_time - first_detection).total_seconds())


@dataclass(frozen=True)
class EvaluationResult:
    discovery: dict[str, float | int | None]
    trail: dict[str, float | int | None]
    procurement: dict[str, float | int | None]
    power: dict[str, float | int | None]
    action: dict[str, float | int | None]
    efficiency: dict[str, float | int | None]
    invariant_status: str = "UNKNOWN"

    def as_dict(self) -> dict[str, Any]:
        return {"discovery": self.discovery, "trail": self.trail, "procurement": self.procurement,
                "power": self.power, "action": self.action, "efficiency": self.efficiency,
                "invariant_status": self.invariant_status}


def evaluate_replay(scenario: Scenario, decisions: tuple[FrozenDecision, ...]) -> EvaluationResult:
    """Evaluate independently observable dimensions; unavailable truth stays unavailable."""
    verified = _verify_decisions(decisions)
    if verified is None:
        invariant_status = "UNKNOWN"
    elif not verified or any(item.action in {"ENGAGE", "READY_FOR_AUTHORIZED_SUBMISSION"}
                             for item in decisions):
        invariant_status = "FAIL"
    else:
        invariant_status = "PASS"
    visible = set().union(*(set(item.visible_evidence_ids) for item in decisions)) if decisions else set()
    expected = scenario.truth.procurement_episode_id
    claims: list[tuple[FrozenDecision, str]] = []
    for decision in decisions:
        claim = decision.forecast.get("discovery")
        if not isinstance(claim, Mapping):
            continue
        episode_id = claim.get("episode_id")
        basis = claim.get("basis_evidence_ids")
        if (isinstance(episode_id, str) and episode_id.strip() and isinstance(basis, (tuple, list))
                and basis and all(isinstance(item, str) and item.strip() for item in basis)
                and set(basis).issubset(decision.visible_evidence_ids)):
            claims.append((decision, episode_id))
    # Count each claimed episode once so repeating a claim cannot improve precision.
    claimed_episode_ids = {episode_id for _, episode_id in claims}
    recognized = expected in claimed_episode_ids
    precision = (int(expected in claimed_episode_ids) / len(claimed_episode_ids)
                 if claimed_episode_ids else None)
    recall = 1.0 if recognized else 0.0
    predicted_states = [item.forecast.get("procurement", {}).get("state") for item in decisions]
    next_event_known = scenario.truth.outcome in predicted_states
    actionable = sum(item.action in {"RESEARCH", "PREPARE", "BID_REVIEW"} for item in decisions)
    # The current evidence contract has no typed episode linkage or
    # customer-action sufficiency field, so visible basis IDs cannot justify
    # useful-lead credit even for PREPARE/BID_REVIEW decisions.
    useful_lead = None
    return EvaluationResult(
        discovery={"precision": precision, "recall": recall, "visible_evidence": len(visible)},
        trail={"episode_resolved": int(recognized), "entity_linkage": None},
        procurement={"next_event_correct": int(next_event_known), "useful_lead_seconds": useful_lead},
        power={"numeric_error_mw": None, "status": "UNAVAILABLE"},
        action={"actionable_steps": actionable, "attention_burden": len(decisions)},
        efficiency={"decision_count": len(decisions)},
        invariant_status=invariant_status,
    )
