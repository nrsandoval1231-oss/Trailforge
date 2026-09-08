"""Serialization boundary for versioned Procurement Arena scenarios."""
from __future__ import annotations
import json
from datetime import datetime
from typing import Any, Mapping
from .foundation import EvidenceEvent, GroundTruth, Scenario

def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("DSL timestamps must include a timezone")
    return parsed

class ScenarioDsl:
    """Parse JSON or YAML mappings without adding a second persistence system."""
    @staticmethod
    def from_mapping(raw: Mapping[str, Any]) -> Scenario:
        if raw.get("schema_version") != "procurement-arena-scenario-v1":
            raise ValueError("unsupported scenario schema_version")
        evidence = tuple(EvidenceEvent(
            evidence_id=item["evidence_id"], source_id=item["source_id"],
            event_date=_time(item["event_date"]), document_date=_time(item["document_date"]),
            verified_available_at=_time(item["verified_available_at"]),
            observed_at=_time(item["observed_at"]), claims=item.get("claims", {}),
            claim_basis=item.get("claim_basis", "UNKNOWN"), source_version=item.get("source_version", ""),
            lineage_family=item.get("lineage_family", ""), is_prediction=item.get("is_prediction", False),
            tenant_id=item.get("tenant_id", "default")
        ) for item in raw.get("evidence", ()))
        truth = raw["truth"]
        return Scenario(raw["scenario_id"], raw["version"], raw["seed"],
            tuple(_time(value) for value in raw["timeline"]), evidence,
            GroundTruth(truth["procurement_episode_id"], truth["outcome"],
                        _time(truth["solicitation_at"]) if truth.get("solicitation_at") else None),
            raw.get("tenant_id", "default"))

    @classmethod
    def loads(cls, text: str, *, format: str = "json") -> Scenario:
        if format == "json":
            raw = json.loads(text)
        elif format in {"yaml", "yml"}:
            try:
                import yaml
            except ImportError as exc:  # pragma: no cover
                raise ValueError("YAML loading requires PyYAML") from exc
            raw = yaml.safe_load(text)
        else:
            raise ValueError("format must be json or yaml")
        if not isinstance(raw, Mapping):
            raise ValueError("scenario document must be an object")
        return cls.from_mapping(raw)

    @staticmethod
    def dumps(scenario: Scenario) -> str:
        """Serialize a validated scenario to canonical JSON."""
        from .foundation import validate_scenario
        validate_scenario(scenario)
        raw = {
            "schema_version": "procurement-arena-scenario-v1",
            "scenario_id": scenario.scenario_id, "version": scenario.version, "seed": scenario.seed,
            "tenant_id": scenario.tenant_id,
            "timeline": [item.isoformat() for item in scenario.timeline],
            "evidence": [{
                "evidence_id": item.evidence_id, "source_id": item.source_id,
                "event_date": item.event_date.isoformat(), "document_date": item.document_date.isoformat(),
                "verified_available_at": item.verified_available_at.isoformat(),
                "observed_at": item.observed_at.isoformat(), "claims": dict(item.claims),
                "claim_basis": str(item.claim_basis), "source_version": item.source_version,
                "lineage_family": item.lineage_family, "is_prediction": item.is_prediction,
                "tenant_id": item.tenant_id,
            } for item in scenario.evidence],
            "truth": {"procurement_episode_id": scenario.truth.procurement_episode_id,
                      "outcome": scenario.truth.outcome,
                      "solicitation_at": scenario.truth.solicitation_at.isoformat() if scenario.truth.solicitation_at else None},
        }
        return json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
