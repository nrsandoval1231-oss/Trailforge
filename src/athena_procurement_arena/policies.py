"""Deterministic policy contract, controls, and the initial BASELINE_A policy."""
from __future__ import annotations

import random
import re
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


def classify_scope(evidence: tuple[Mapping[str, Any], ...]) -> str:
    """Classify scope; maintenance-only work is outside the commercial target."""
    text = _text(evidence)
    maintenance = any(term in text for term in ("maintenance", "maintain", "repair", "service"))
    in_scope = any(term in text for term in (
        "temporary", "rental", "install", "installation", "replace", "replacement",
        "new generator", "emergency generation", "standby generator", "power generation",
    ))
    if maintenance and not in_scope:
        return "OUT_OF_SCOPE_MAINTENANCE_ONLY"
    if in_scope:
        return "IN_SCOPE_INSTALLATION_OR_TEMPORARY_POWER"
    return "UNKNOWN"


def _scope(state: Mapping[str, Any]) -> str:
    return classify_scope(tuple(state.get("visible_evidence", ())))


def classify_target(evidence: tuple[Mapping[str, Any], ...], *, minimum_kw: int = 300) -> str:
    """Qualify continuous prime-power opportunities for the commercial target."""
    scope = classify_scope(evidence)
    text = _text(evidence)
    normalized = text.replace("_", " ")
    if scope == "OUT_OF_SCOPE_MAINTENANCE_ONLY":
        return scope
    if any(term in normalized for term in ("emergency backup", "emergency standby", "standby-only", "backup-only")):
        return "OUT_OF_SCOPE_EMERGENCY_BACKUP"
    ratings_kw = []
    for item in evidence:
        claims = _get(item, "claims", {})
        if isinstance(claims, Mapping):
            for key, value in claims.items():
                if key.lower() in {"required_kw", "prime_kw", "generator_kw", "capacity_kw"} and isinstance(value, (int, float)):
                    ratings_kw.append(float(value))
                if key.lower() in {"required_mw", "prime_mw", "generator_mw", "capacity_mw"} and isinstance(value, (int, float)):
                    ratings_kw.append(float(value) * 1000)
    for number, unit in re.findall(r"(?<!\d)(\d+(?:\.\d+)?)\s*(kw|mw)\b", normalized):
        ratings_kw.append(float(number) * (1000 if unit == "mw" else 1))
    if not ratings_kw:
        return "UNKNOWN_TARGET_REQUIREMENTS"
    if max(ratings_kw) < minimum_kw:
        return "OUT_OF_SCOPE_BELOW_300KW"
    if "prime" not in normalized:
        return "OUT_OF_SCOPE_NOT_PRIME"
    if scope != "IN_SCOPE_INSTALLATION_OR_TEMPORARY_POWER":
        return "UNKNOWN_TARGET_REQUIREMENTS"
    return "IN_SCOPE_PRIME_POWER_300KW_PLUS"


def _target_allowed(state: Mapping[str, Any]) -> bool:
    return classify_target(tuple(state.get("visible_evidence", ()))) == "IN_SCOPE_PRIME_POWER_300KW_PLUS"


def keyword_rfp(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    evidence = state.get("visible_evidence", ())
    scope = _scope(state)
    if not _target_allowed(state):
        return {"solicitation_detected": False, "scope": scope, "score": 0}, "IGNORE"
    text = _text(evidence)
    hit = any(word in text for word in ("rfp", "request for proposal", "solicitation"))
    return {"solicitation_detected": hit, "score": 1 if hit else 0}, "BID_REVIEW" if hit else "IGNORE"


def static_weighted_score(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    scope = _scope(state)
    if not _target_allowed(state):
        return {"scope": scope, "score": 0}, "IGNORE"
    text = _text(state.get("visible_evidence", ()))
    weights = {"capital": 2, "funded": 2, "permit": 1, "engineering": 1, "rfp": 4, "budget": 2}
    score = sum(weight for word, weight in weights.items() if word in text)
    return {"score": score}, "PREPARE" if score >= 4 else ("RESEARCH" if score else "IGNORE")


def latest_event(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    evidence = state.get("visible_evidence", ())
    if not _target_allowed(state):
        return {"latest_evidence_id": None, "scope": _scope(state)}, "IGNORE"
    latest = max(evidence, key=lambda item: _get(item, "event_date", ""), default=None)
    return {"latest_evidence_id": _get(latest, "evidence_id") if latest else None}, "WATCH" if latest else "IGNORE"


def buyer_frequency(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    if not _target_allowed(state):
        return {"buyer_event_count": 0, "scope": _scope(state)}, "IGNORE"
    buyers = [_get(item, "claims", {}).get("buyer") for item in state.get("visible_evidence", ())]
    count = Counter(x for x in buyers if x)
    recurring = max(count.values(), default=0) >= 3
    return {"buyer_event_count": max(count.values(), default=0)}, "RESEARCH" if recurring else "IGNORE"


def seeded_random_eligible(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    if not _target_allowed(state):
        return {"selected_evidence_id": None, "scope": _scope(state)}, "IGNORE"
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
        evidence = tuple({"claims": claim} for claim in trail["claims"])
        return {"hits": hits, "scope": classify_scope(evidence), "target_scope": classify_target(evidence),
                "entity_count": len(trail["entities"]), "text": text,
                "required_mw": max(required, default=None), "supply_mw": max(supply, default=None)}

    def forecastProcurement(self, patterns):
        hits = set(patterns["hits"])
        if patterns["target_scope"].startswith("OUT_OF_SCOPE"):
            state = "OUT_OF_SCOPE"
        elif hits and not (hits - {"amendment"}):
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
        return {"state": state, "confidence": min(1.0, len(hits) / 5), "target_scope": patterns["target_scope"]}

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
        if state == "OUT_OF_SCOPE" or procurement.get("target_scope") != "IN_SCOPE_PRIME_POWER_300KW_PLUS":
            return "IGNORE"
        if state == "SOLICITATION_RELEASED":
            return "BID_REVIEW"
        if power.get("status") == "GAP" and state not in {"CANCELLED", "DEFERRED"}:
            return "PREPARE"
        if state in {"FUNDED", "ENGINEERING", "REBID_EXPECTED"}:
            return "PREPARE"
        if research["budget"]:
            return "RESEARCH"
        return "IGNORE"


class PreRfpBaselineV1:
    """Minimal source-backed precursor baseline; consumes only visible typed claims."""

    policy_id = "PRE_RFP_BASELINE_V1"
    version = "1.0"

    @staticmethod
    def _known_text(value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip()) and value.strip().casefold() != "unknown"

    def __call__(self, state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
        evidence = tuple(state.get("visible_evidence", ()))
        claims_by_id = tuple((_get(item, "evidence_id"), _get(item, "claims", {})) for item in evidence)
        suppressors = {"generation_not_in_scope", "awarded", "supply_resolved"}
        suppressed = tuple(evidence_id for evidence_id, claims in claims_by_id
                           if any(claims.get(key) is True for key in suppressors))
        if suppressed:
            return {"decision": "SUPPRESS", "basis_evidence_ids": list(suppressed)}, "IGNORE"
        qualifying = tuple(
            evidence_id for evidence_id, claims in claims_by_id
            if claims.get("project_specific") is True
            and claims.get("generation_need_supported") is True
            and self._known_text(claims.get("need_reason"))
            and self._known_text(claims.get("buyer_organization"))
        )
        if qualifying:
            return {"decision": "INVESTIGATE", "basis_evidence_ids": list(qualifying),
                    "power_need_mw": None, "power_need_status": "UNKNOWN"}, "RESEARCH"
        return {"decision": "WATCH", "basis_evidence_ids": [],
                "power_need_mw": None, "power_need_status": "UNKNOWN"}, "IGNORE"
