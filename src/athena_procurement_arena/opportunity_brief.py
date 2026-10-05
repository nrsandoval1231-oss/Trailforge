"""Deterministic operator brief derived from a retained opportunity record.

The brief separates cited facts, operator inference, and unknowns, gives a
pre-RFP signal its own qualification verdict, and derives one next action from
record state.  It reads stored fields only: no network, no scoring, no outreach.
"""
from __future__ import annotations

from typing import Any

PRIMARY_SOURCE_TYPES = frozenset({
    "official-solicitation", "official-source", "procurement-portal", "planning-record",
    "permit", "utility-document", "owner-publication",
})
EXCLUDED_BUYER_TYPES = frozenset({"COMPETITOR", "RERENTER"})
BUYER_TYPES = EXCLUDED_BUYER_TYPES | {"OWNER", "DEVELOPER", "EPC", "GC", "UTILITY", "OTHER"}


def _facts(record: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []

    def add(field: str, value: Any, citation: dict[str, Any] | None) -> None:
        if citation:
            facts.append({"field": field, "value": value, "quote": citation["quote"],
                          "source_url": citation.get("source_url"), "capture_sha256": citation.get("capture_sha256")})

    for field, citation in record.get("field_evidence", {}).items():
        value = record.get("title") if field == "title" else record.get("identity", {}).get(field.removeprefix("identity."))
        add(field, record.get(field) if field in {"direct_buyer_orgs", "roles", "procurement_route"} else value, citation)
    for field, value in record.get("requirements", {}).items():
        if value is not None and value != []:
            add(f"requirements.{field}", value, record.get("requirement_quotes", {}).get(field))
    for field in ("published_at", "deadline", "earliest_signal"):
        claim = record.get(field)
        if claim:
            add(field, claim.get("value"), claim)
    return facts


def _source_types(record: dict[str, Any]) -> set[str]:
    return {str(source.get("source_type") or "").lower() for source in record.get("sources", {}).values()}


def pre_rfp_qualification(record: dict[str, Any]) -> dict[str, Any]:
    """Qualify a pre-RFP signal from cited evidence only; news alone never qualifies."""
    reasons: list[str] = []
    if str(record.get("buyer_type") or "").upper() in EXCLUDED_BUYER_TYPES:
        return {"status": "EXCLUDED_BUYER", "reason_codes": ["BUYER_IS_COMPETITOR_OR_RERENTER"]}
    if not _source_types(record) & PRIMARY_SOURCE_TYPES:
        return {"status": "RESEARCH_TARGET_ONLY", "reason_codes": ["NO_PRIMARY_SOURCE_CAPTURED"]}
    fuel = str((record.get("requirements") or {}).get("fuel") or "").lower()
    if any(term in fuel for term in ("diesel", "light fuel oil", "lfo")):
        return {"status": "NOT_FIT", "reason_codes": ["INCOMPATIBLE_FUEL_CITED"]}
    if record.get("identity_resolution") != "RESOLVED":
        reasons.append("PROJECT_IDENTITY_UNRESOLVED")
    if not any(value not in (None, []) for value in record.get("requirements", {}).values()):
        reasons.append("POWER_RELEVANCE_NOT_CITED")
    if reasons:
        return {"status": "NEEDS_REVIEW", "reason_codes": reasons}
    if not record.get("direct_buyer_orgs") and not record.get("procurement_route"):
        return {"status": "SIGNAL_CANDIDATE", "reason_codes": ["PRIMARY_SOURCE", "POWER_RELEVANCE_CITED",
                                                                "BUYER_ROUTE_NOT_EVIDENCED"]}
    return {"status": "ACTIONABLE_SIGNAL", "reason_codes": ["PRIMARY_SOURCE", "POWER_RELEVANCE_CITED",
                                                            "BUYER_ROUTE_EVIDENCED"]}


def _unknowns(record: dict[str, Any]) -> list[str]:
    unknowns = [f"requirements.{field}" for field in record.get("missing_information", [])]
    if not record.get("deadline"):
        unknowns.append("deadline")
    if not record.get("direct_buyer_orgs"):
        unknowns.append("direct_buyer_orgs")
    if not record.get("procurement_route"):
        unknowns.append("procurement_route")
    for field in sorted(record.get("requirement_conflicts", {})):
        unknowns.append(f"requirements.{field} (conflicting sources)")
    for field in sorted(record.get("date_conflicts", {})):
        unknowns.append(f"{field} (conflicting sources)")
    return list(dict.fromkeys(unknowns))


def _next_action(record: dict[str, Any], qualification: dict[str, Any]) -> str:
    status = qualification.get("status")
    buyer = ", ".join(map(str, record.get("direct_buyer_orgs", []))) or "the evidenced buyer"
    if status == "EXCLUDED_BUYER":
        return "Do not pursue: the evidenced buyer is a competitor or re-renter."
    if status == "RESEARCH_TARGET_ONLY":
        return ("Find a primary source (planning record, permit, utility document, owner publication or "
                "solicitation) for this project before any outreach.")
    if status in {"NOT_CURRENT", "NOT_FIT"}:
        return "Keep as historical research only; do not pursue."
    if record.get("requirement_conflicts") or record.get("date_conflicts"):
        return "Resolve the conflicting source values against the originals before any other step."
    if record["kind"] == "ACTIVE_RFP":
        if status != "POTENTIAL_FIT_PENDING_HUMAN_REVIEW":
            return ("Re-capture the solicitation page with max-age 0 and confirm the deadline, amendments and "
                    "required capacity on the issuing portal.")
        return f"Read the solicitation documents, confirm amendments, and decide bid/no-bid with {buyer}'s published route."
    if status == "NEEDS_REVIEW":
        return "Resolve the open review reasons (project identity or cited power relevance) from primary sources."
    if status == "SIGNAL_CANDIDATE":
        return "Identify the owner, EPC or utility procurement route from primary documents; no outreach yet."
    return f"Draft a role-specific, pain-point-led note to {buyer} for operator approval; nothing is sent."


def build_brief(record: dict[str, Any], qualification: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return facts, inference, unknowns, qualification and next action for one record."""
    if record["kind"] == "PRE_RFP_PROJECT":
        qualification = pre_rfp_qualification(record)
    elif qualification is None:
        qualification = record.get("qualification") or {"status": "NEEDS_REVIEW", "reason_codes": []}
    hypothesis = record.get("power_gap_hypothesis")
    return {
        "opportunity_type": "ACTIVE_RFP" if record["kind"] == "ACTIVE_RFP" else "PRE_RFP_SIGNAL",
        "qualification": qualification,
        "facts": _facts(record),
        "inferences": ([{"statement": hypothesis, "basis": "OPERATOR_HYPOTHESIS_UNCITED"}] if hypothesis else []),
        "unknowns": _unknowns(record),
        "next_action": _next_action(record, qualification),
    }
