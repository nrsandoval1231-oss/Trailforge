"""Deterministic policy contract, controls, and the initial BASELINE_A policy."""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Mapping
from typing import Any


class PolicyContract(ABC):
    policy_id = ""
    version = "1"

    def run(self, state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
        evidence = self.observe(state)
        entities = self.resolveEntities(evidence)
        trail = self.updateTrail(entities)
        patterns = self.detectPatterns(trail)
        procurement = self.forecastProcurement(patterns)
        power = self.forecastPowerNeed(patterns)
        research = self.chooseResearch(patterns)
        action = self.recommendAction(procurement, power, research)
        return {"procurement": procurement, "power": power, "research": research,
                "patterns": patterns}, action

    @abstractmethod
    def observe(self, state): ...
    @abstractmethod
    def resolveEntities(self, evidence): ...
    @abstractmethod
    def updateTrail(self, entities): ...
    @abstractmethod
    def detectPatterns(self, trail): ...
    @abstractmethod
    def forecastProcurement(self, patterns): ...
    @abstractmethod
    def forecastPowerNeed(self, patterns): ...
    @abstractmethod
    def chooseResearch(self, patterns): ...
    @abstractmethod
    def recommendAction(self, procurement, power, research): ...

    def __call__(self, state):
        return self.run(state)


def _text(evidence: tuple[Mapping[str, Any], ...]) -> str:
    return " ".join(str(item.get("claims", {}) if isinstance(item, Mapping) else item.claims).lower() for item in evidence)

def _get(item: Any, name: str, default: Any = None) -> Any:
    return item.get(name, default) if isinstance(item, Mapping) else getattr(item, name, default)


def keyword_rfp(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    evidence = state.get("visible_evidence", ())
    text = _text(evidence)
    hit = any(word in text for word in ("rfp", "request for proposal", "solicitation"))
    return {"solicitation_detected": hit, "score": 1 if hit else 0}, "BID_REVIEW" if hit else "IGNORE"


def static_weighted_score(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    text = _text(state.get("visible_evidence", ()))
    weights = {"capital": 2, "funded": 2, "permit": 1, "engineering": 1, "rfp": 4, "budget": 2}
    score = sum(weight for word, weight in weights.items() if word in text)
    return {"score": score}, "PREPARE" if score >= 4 else ("RESEARCH" if score else "IGNORE")


def latest_event(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    evidence = state.get("visible_evidence", ())
    latest = max(evidence, key=lambda item: _get(item, "event_date", ""), default=None)
    return {"latest_evidence_id": _get(latest, "evidence_id") if latest else None}, "WATCH" if latest else "IGNORE"


def buyer_frequency(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    buyers = [_get(item, "claims", {}).get("buyer") for item in state.get("visible_evidence", ())]
    count = Counter(x for x in buyers if x)
    recurring = max(count.values(), default=0) >= 3
    return {"buyer_event_count": max(count.values(), default=0)}, "RESEARCH" if recurring else "IGNORE"


def seeded_random_eligible(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    eligible = sorted(_get(item, "evidence_id", "") for item in state.get("visible_evidence", ()))
    rng = random.Random(int(state.get("seed", 0)) + len(eligible))
    selected = rng.choice(eligible) if eligible else None
    return {"selected_evidence_id": selected}, "WATCH" if selected else "IGNORE"


class BaselineA(PolicyContract):
    policy_id = "BASELINE_A"
    version = "1.0"

    def observe(self, state):
        return tuple(state.get("visible_evidence", ()))

    def resolveEntities(self, evidence):
        return tuple({"evidence_id": _get(item, "evidence_id"), "claims": _get(item, "claims", {}),
                      "lineage_family": _get(item, "lineage_family", "")}
                     for item in evidence)

    def updateTrail(self, entities):
        return {"entities": entities, "text": _text(tuple({"claims": e["claims"]} for e in entities)),
                "claims": tuple(e["claims"] for e in entities)}

    def detectPatterns(self, trail):
        text = trail["text"]
        terms = ("capital", "funded", "permit", "engineering", "rfp", "solicitation", "recompete", "rebid",
                 "private", "rfq", "direct", "renewal", "extension", "deferred", "cancelled", "cross_project",
                 "amendment", "power", "generator", "mw", "readiness_fail")
        hits = tuple(term for term in terms if term in text)
        required = [claim.get("required_mw") for claim in trail["claims"] if isinstance(claim.get("required_mw"), (int, float))]
        supply = [claim.get("supply_mw") for claim in trail["claims"] if isinstance(claim.get("supply_mw"), (int, float))]
        return {"hits": hits, "entity_count": len(trail["entities"]), "text": text,
                "required_mw": max(required, default=None), "supply_mw": max(supply, default=None)}

    def forecastProcurement(self, patterns):
        hits = set(patterns["hits"])
        if hits and not (hits - {"amendment"}):
            state = "UNKNOWN"
        elif "cancelled" in hits:
            state = "CANCELLED"
        elif "deferred" in hits:
            state = "DEFERRED"
        elif "private" in hits or "rfq" in hits:
            state = "PRIVATE_PROCUREMENT"
        elif "direct" in hits or "renewal" in hits:
            state = "DIRECT_AWARD"
        elif "extension" in hits:
            state = "EXTENDED"
        elif "rfp" in hits or "solicitation" in hits:
            state = "SOLICITATION_RELEASED"
        elif "recompete" in hits or "rebid" in hits:
            state = "REBID_EXPECTED"
        elif {"capital", "funded"}.issubset(hits):
            state = "FUNDED"
        elif "engineering" in hits or "permit" in hits:
            state = "ENGINEERING"
        elif hits:
            state = "EARLY_SIGNAL"
        else:
            state = "UNKNOWN"
        return {"state": state, "confidence": min(1.0, len(hits) / 5)}

    def forecastPowerNeed(self, patterns):
        text = patterns["text"]
        if "mw" not in text and "generator" not in text and "power" not in text:
            return {"status": "UNKNOWN", "peak_gap_mw": None}
        required, supply = patterns.get("required_mw"), patterns.get("supply_mw")
        if required is not None and supply is not None:
            return {"status": "GAP" if required > supply else "NO_GAP",
                    "peak_gap_mw": max(0.0, required - supply)}
        return {"status": "UNKNOWN", "peak_gap_mw": None, "reason": "supply or load not quantified"}

    def chooseResearch(self, patterns):
        return {"priority": "HIGH" if patterns["hits"] else "LOW", "budget": 1 if patterns["hits"] else 0}

    def recommendAction(self, procurement, power, research):
        state = procurement["state"]
        if state == "SOLICITATION_RELEASED":
            return "BID_REVIEW"
        if power.get("status") == "GAP" and state not in {"CANCELLED", "DEFERRED"}:
            return "PREPARE"
        if state in {"FUNDED", "ENGINEERING", "REBID_EXPECTED"}:
            return "PREPARE"
        if research["budget"]:
            return "RESEARCH"
        return "IGNORE"
