from datetime import UTC, datetime

from athena_procurement_arena import (
    BaselineA,
    EvidenceEvent,
    GroundTruth,
    Scenario,
    TemporalWorld,
    buyer_frequency,
    classify_target,
    keyword_rfp,
    latest_event,
    seeded_random_eligible,
    static_weighted_score,
)
from athena_procurement_arena.policies import classify_scope
from athena_procurement_arena.scenarios import family_scenario, family_scope

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
                          {"private": "rfq", "extension": True, "temporary": "prime power",
                           "prime_power": "continuous", "required_mw": 10, "supply_mw": 4})
    state = {"visible_evidence": (event,), "seed": 1}
    forecast, action = BaselineA()(state)
    assert forecast["procurement"]["state"] == "PRIVATE_PROCUREMENT"
    assert forecast["power"] == {"status": "GAP", "peak_gap_mw": 6}
    assert action == "PREPARE"


def test_maintenance_only_is_excluded_but_installation_with_maintenance_is_eligible():
    maintenance = EvidenceEvent("maintenance", "s", T0, T0, T0, T0,
                                {"generator": "maintenance services"})
    install = EvidenceEvent("install", "s", T0, T0, T0, T0,
                            {"generator": "replacement installation with maintenance", "temporary": "power",
                             "prime_power": "continuous", "required_kw": 300})
    maintenance_state = {"visible_evidence": (maintenance,), "seed": 1}
    install_state = {"visible_evidence": (install,), "seed": 1}
    policies = (keyword_rfp, static_weighted_score, latest_event, buyer_frequency,
                seeded_random_eligible, BaselineA())
    assert classify_scope((maintenance,)) == "OUT_OF_SCOPE_MAINTENANCE_ONLY"
    assert all(policy(maintenance_state)[1] == "IGNORE" for policy in policies)
    assert classify_scope((install,)) == "IN_SCOPE_INSTALLATION_OR_TEMPORARY_POWER"
    assert BaselineA()(install_state)[1] in {"RESEARCH", "PREPARE", "BID_REVIEW"}


def test_family_corpus_carries_commercial_scope_labels():
    maintenance = family_scenario("service_on_time", 4).evidence
    installation = family_scenario("replacement_temporary_generation", 4).evidence
    assert family_scope("service_on_time") == "MAINTENANCE_ONLY"
    assert family_scope("replacement_temporary_generation") == "TEMPORARY_POWER_OR_INSTALLATION"
    assert BaselineA()({"visible_evidence": maintenance, "seed": 4})[1] == "IGNORE"
    assert BaselineA()({"visible_evidence": installation, "seed": 4})[1] in {"RESEARCH", "PREPARE", "BID_REVIEW"}


def test_target_requires_prime_power_at_least_300kw_and_not_backup_only():
    def event(evidence_id, claims):
        return EvidenceEvent(evidence_id, "s", T0, T0, T0, T0, claims)

    qualified = event("qualified", {"temporary": "power", "prime": True, "required_kw": 300})
    below = event("below", {"temporary": "power", "prime": True, "required_kw": 299})
    backup = event("backup", {"emergency_backup": True, "prime": True, "required_kw": 500})
    assert classify_target((qualified,)) == "IN_SCOPE_PRIME_POWER_300KW_PLUS"
    assert classify_target((below,)) == "OUT_OF_SCOPE_BELOW_300KW"
    assert classify_target((backup,)) == "OUT_OF_SCOPE_EMERGENCY_BACKUP"
    assert BaselineA()({"visible_evidence": (below,), "seed": 1})[1] == "IGNORE"
    assert BaselineA()({"visible_evidence": (backup,), "seed": 1})[1] == "IGNORE"
