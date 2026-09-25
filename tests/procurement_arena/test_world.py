from datetime import UTC, datetime, timedelta

import pytest

from athena_procurement_arena import (
    ActionSupportAttestation,
    EvidenceEvent,
    GroundTruth,
    InvariantViolation,
    Scenario,
    ScenarioDsl,
    TemporalWorld,
    validate_scenario,
)

T0 = datetime(2026, 1, 1, tzinfo=UTC)

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

@pytest.mark.parametrize("action", ["ENGAGE", "READY_FOR_AUTHORIZED_SUBMISSION"])
def test_world_rejects_unapproved_consequential_actions_without_recording(action):
    world = TemporalWorld(scenario(), "test", lambda state: ({}, action))
    with pytest.raises(InvariantViolation, match="I-10"):
        world.step()
    assert world.ledger.records == ()
    assert world._cursor == -1

def test_same_seed_and_inputs_replay_identically():
    first, second = TemporalWorld(scenario(), "BASELINE_A", policy), TemporalWorld(scenario(), "BASELINE_A", policy)
    first.run()
    second.run()
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

def test_provenance_fields_round_trip_without_losing_contradictions():
    item = EvidenceEvent("prov", "source", T0, T0, T0, T0, authority="PUBLIC_AUTHORITY",
                         source_spans=("line 1",), entity_candidates=("project-1",),
                         permission_scope="TENANT", contradictions=("e2",))
    source = Scenario("prov", "1", 1, (T0,), (item,), GroundTruth("p", "OPEN"), tenant_id="default")
    loaded = ScenarioDsl.loads(ScenarioDsl.dumps(source))
    assert loaded.evidence[0].source_spans == ("line 1",) and loaded.evidence[0].contradictions == ("e2",)


def test_action_support_attestation_round_trips_with_stable_scenario_hash():
    attestation = ActionSupportAttestation("episode-1", "PREPARE", "reviewer", T0,
                                          "line 1", "Specific supported basis")
    item = EvidenceEvent("reviewed", "source", T0, T0, T0, T0, source_spans=("line 1",),
                         action_support=attestation)
    original = Scenario("reviewed", "1", 1, (T0,), (item,), GroundTruth("episode-1", "OPEN"))
    serialized = ScenarioDsl.dumps(original)
    loaded = ScenarioDsl.loads(serialized)
    assert loaded.evidence[0].action_support == attestation
    assert validate_scenario(loaded) == validate_scenario(original)
