from datetime import datetime, timedelta, timezone
from athena_procurement_arena import EvidenceEvent, GroundTruth, Scenario, ScenarioDsl, TemporalWorld, validate_scenario

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

def test_dsl_round_trip_preserves_scenario_hash():
    original = scenario()
    assert validate_scenario(ScenarioDsl.loads(ScenarioDsl.dumps(original))) == validate_scenario(original)

def test_checked_in_fixture_is_versioned_and_valid():
    from pathlib import Path
    loaded = ScenarioDsl.loads(Path("scenarios/fixtures/smoke.json").read_text(encoding="utf-8"))
    assert loaded.scenario_id == "fixture-smoke" and validate_scenario(loaded)
    assert validate_scenario(ScenarioDsl.loads(ScenarioDsl.dumps(loaded))) == validate_scenario(loaded)
