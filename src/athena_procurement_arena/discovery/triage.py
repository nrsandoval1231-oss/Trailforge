"""Relevance ranking that orders human attention and decides nothing.

Triage is a coarse keyword heuristic over listing text.  It exists so a reviewer
reads the twenty most promising rows before the six hundredth, and it is
deliberately separate from `screen_aura_rental_candidate`: a high score is not a
qualification and a zero score is not a rejection.  Only the fail-closed screen,
run against captured evidence, decides whether a record can be shortlisted.
"""
from __future__ import annotations

from dataclasses import dataclass

# Weighted toward planned, schedule-driven power rather than equipment supply.
TRIAGE_TERMS: dict[str, int] = {
    "temporary power": 5,
    "temporary generation": 5,
    "bridge power": 5,
    "commissioning power": 5,
    "construction power": 5,
    "interim power": 4,
    "energization": 4,
    "interconnection delay": 4,
    "utility delay": 4,
    "generator rental": 4,
    "rental generator": 4,
    "load bank": 3,
    "commissioning": 3,
    "substation": 3,
    "switchgear": 2,
    "data center": 3,
    "energization schedule": 3,
    "prime power": 3,
    "natural gas": 2,
    "propane": 2,
    "megawatt": 2,
    "kilowatt": 1,
    "generator": 1,
}

# Patterns that usually mean the work is not Aura-shaped.  They lower rank so a
# reviewer sees them later; they never remove a row from the queue.
NEGATIVE_TERMS: dict[str, int] = {
    "maintenance and repair": -4,
    "preventive maintenance": -4,
    "maintenance services": -3,
    "load bank testing services": -2,
    "emergency standby": -3,
    "standby generator": -2,
    "generator maintenance": -4,
    "power purchase agreement": -5,
    "annual service contract": -3,
}


@dataclass(frozen=True)
class TriageScore:
    score: int
    matched: tuple[str, ...]
    penalized: tuple[str, ...]

    @property
    def band(self) -> str:
        if self.score >= 8:
            return "HIGH"
        if self.score >= 4:
            return "MEDIUM"
        if self.score >= 1:
            return "LOW"
        return "NONE"

    def as_dict(self) -> dict[str, object]:
        return {"score": self.score, "band": self.band,
                "matched": list(self.matched), "penalized": list(self.penalized)}


def triage_score(text: str) -> TriageScore:
    """Rank listing text for reviewer attention. Never a qualification decision."""
    haystack = " ".join(text.split()).lower()
    matched = tuple(term for term in TRIAGE_TERMS if term in haystack)
    penalized = tuple(term for term in NEGATIVE_TERMS if term in haystack)
    score = sum(TRIAGE_TERMS[term] for term in matched)
    score += sum(NEGATIVE_TERMS[term] for term in penalized)
    return TriageScore(max(score, 0), matched, penalized)
