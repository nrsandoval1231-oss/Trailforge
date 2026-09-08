from datetime import UTC, datetime

from athena_procurement_arena import (
    BaselineA,
    EvidenceEvent,
    GroundTruth,
    Scenario,
    TemporalWorld,
    buyer_frequency,
    keyword_rfp,
    latest_event,
    seeded_random_eligible,
    static_weighted_score,
)
from athena_procurement_arena.policies import classify_scope

T0 = datetime(2026, 1, 1, tzinfo=UTC)

def test_baseline_uses_only_visible_evidence_and_contract_is_deterministic():
    early = EvidenceEvent("e1", "s", T0, T0, T0, T0, {"capital": "funded engineering"})
    late = EvidenceEvent("e2", "s", T0, T0, T0.replace(day=3), T0.replace(day=3), {"rfp": True})
    scenario = Scenario("policy", "1", 4, (T0, T0.replace(day=3)), (early, late), GroundTruth("p", "OPEN"))
    world = TemporalWorld(scenario, BaselineA.policy_id, BaselineA())
    records = world.run()
    assert records[0].visible_evidence_ids == ("e1",)
    assert records[1].visible_evidence_ids == ("e1", "e2")
    assert world.ledger.records[0].forecast["procurement"]["state"] == "FUNDED"
    assert world.ledger.records[1].forecast["procurement"]["state"] == "SOLICITATION_RELEASED"

def test_keyword_control_is_conservative():
    assert keyword_rfp({"visible_evidence": (), "seed": 1})[1] == "IGNORE"

def test_baseline_handles_routes_extensions_and_power_mismatch():
    event = EvidenceEvent("complex", "s", T0, T0, T0, T0,
                          {"private": "rfq", "extension": True, "required_mw": 10, "supply_mw": 4})
    state = {"visible_evidence": (event,), "seed": 1}
    forecast, action = BaselineA()(state)
    assert forecast["procurement"]["state"] == "PRIVATE_PROCUREMENT"
    assert forecast["power"] == {"status": "GAP", "peak_gap_mw": 6}
    assert action == "PREPARE"


def test_maintenance_only_is_excluded_but_installation_with_maintenance_is_eligible():
    maintenance = EvidenceEvent("maintenance", "s", T0, T0, T0, T0,
                                {"generator": "maintenance services"})
    install = EvidenceEvent("install", "s", T0, T0, T0, T0,
                            {"generator": "replacement installation with maintenance"})
    maintenance_state = {"visible_evidence": (maintenance,), "seed": 1}
    install_state = {"visible_evidence": (install,), "seed": 1}
    policies = (keyword_rfp, static_weighted_score, latest_event, buyer_frequency,
                seeded_random_eligible, BaselineA())
    assert classify_scope((maintenance,)) == "OUT_OF_SCOPE_MAINTENANCE_ONLY"
    assert all(policy(maintenance_state)[1] == "IGNORE" for policy in policies)
    assert classify_scope((install,)) == "IN_SCOPE_INSTALLATION_OR_TEMPORARY_POWER"
    assert BaselineA()(install_state)[1] in {"RESEARCH", "PREPARE", "BID_REVIEW"}
