from datetime import datetime, timedelta, timezone
from athena_procurement_arena import EvidenceEvent, GroundTruth, Scenario, ScenarioDsl, TemporalWorld

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

def scenario():
    return Scenario("world", "1", 99, (T0, T0 + timedelta(days=1)), (
        EvidenceEvent("early", "s", T0, T0, T0, T0),
        EvidenceEvent("late", "s", T0, T0, T0 + timedelta(days=1), T0 + timedelta(days=1)),
    ), GroundTruth("p", "OPEN"))

def policy(state):
    return ({"count": len(state["visible_evidence_ids"])}, "WATCH")

def test_world_reveals_only_available_evidence_and_freezes_each_step():
    world = TemporalWorld(scenario(), "BASELINE_A", policy)
    observations = world.run()
    assert observations[0].visible_evidence_ids == ("early",)
    assert observations[1].visible_evidence_ids == ("early", "late")
    assert len(world.ledger.records) == 2 and world.ledger.verify()

def test_same_seed_and_inputs_replay_identically():
    first, second = TemporalWorld(scenario(), "BASELINE_A", policy), TemporalWorld(scenario(), "BASELINE_A", policy)
    first.run(); second.run()
    assert first.scenario_hash == second.scenario_hash
    assert first.replay_hash() == second.replay_hash()

def test_dsl_loads_versioned_json():
    text = '{"schema_version":"procurement-arena-scenario-v1","scenario_id":"s","version":"1","seed":1,"timeline":["2026-01-01T00:00:00+00:00"],"evidence":[],"truth":{"procurement_episode_id":"p","outcome":"OPEN"}}'
    loaded = ScenarioDsl.loads(text)
    assert loaded.scenario_id == "s" and loaded.timeline == (T0,)
