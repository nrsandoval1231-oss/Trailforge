from datetime import UTC, datetime

from athena_procurement_arena import (
    BaselineA,
    EvidenceEvent,
    GroundTruth,
    Scenario,
    TemporalWorld,
    keyword_rfp,
)

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
