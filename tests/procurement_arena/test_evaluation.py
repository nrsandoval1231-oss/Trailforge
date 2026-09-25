from dataclasses import replace
from datetime import UTC, datetime, timedelta

from athena_procurement_arena import (
    ActionSupportAttestation,
    BaselineA,
    EvidenceEvent,
    FrozenDecision,
    FrozenDecisionLedger,
    GroundTruth,
    Scenario,
    TemporalWorld,
)
from athena_procurement_arena.evaluation import (
    attention_metrics,
    evaluate_power_profile,
    evaluate_replay,
    useful_lead_time_seconds,
)


def test_evaluator_keeps_component_metrics_separate_and_unknown_power_explicit():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    event = EvidenceEvent("p1", "s", t, t, t, t, {"funded": True})
    scenario = Scenario("eval", "1", 3, (t,), (event,), GroundTruth("p1", "FUNDED"))
    world = TemporalWorld(scenario, BaselineA.policy_id, BaselineA())
    world.run()
    result = evaluate_replay(scenario, world.ledger.records)
    assert set(result.as_dict()) == {"discovery", "trail", "procurement", "power", "action", "efficiency", "invariant_status"}
    assert result.power["status"] == "UNAVAILABLE"
    assert result.discovery["precision"] is None
    assert result.discovery["recall"] == 0.0
    assert result.invariant_status == "PASS"

def test_evaluator_fails_on_corrupt_ledger_and_keeps_missing_basis_unknown():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    scenario = Scenario("eval", "1", 3, (t,), (), GroundTruth("p1", "FUNDED"))
    world = TemporalWorld(scenario, BaselineA.policy_id, BaselineA())
    world.run()
    assert evaluate_replay(scenario, ()).invariant_status == "UNKNOWN"
    corrupted = (replace(world.ledger.records[0], record_hash="bad"),)
    assert evaluate_replay(scenario, corrupted).invariant_status == "FAIL"

def test_evaluator_fails_verified_unauthorized_actions():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    scenario = Scenario("eval", "1", 3, (t,), (), GroundTruth("p1", "FUNDED"))
    for action in ("ENGAGE", "READY_FOR_AUTHORIZED_SUBMISSION"):
        ledger = FrozenDecisionLedger()
        ledger.append(FrozenDecision("eval", t, "policy", (), {}, action))
        assert ledger.verify()
        assert evaluate_replay(scenario, ledger.records).invariant_status == "FAIL"

def test_power_evaluator_reports_numeric_error_only_for_verified_truth():
    profile = ({"gap_mw": 6}, {"gap_mw": 0})
    assert evaluate_power_profile(profile, 6)["peak_gap_error_mw"] == 0
    assert evaluate_power_profile(profile, None)["status"] == "UNAVAILABLE"


def test_power_evaluator_does_not_score_partially_unknown_peak():
    profile = ({"gap_mw": 6}, {"gap_mw": None, "status": "UNKNOWN"})
    result = evaluate_power_profile(profile, 6)
    assert result == {"status": "UNKNOWN", "peak_gap_error_mw": None}

def test_attention_metrics_penalize_alert_everything():
    metrics = attention_metrics(tuple(f"t{i}" for i in range(60)), frozenset({"t59"}))
    assert metrics["5"]["precision"] == 0 and metrics["50"]["recall"] == 0
    assert metrics["50"]["precision"] == 0

def test_useful_lead_time_requires_actionable_detection():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    assert useful_lead_time_seconds(t + timedelta(days=5), t, actionable=False) is None
    assert useful_lead_time_seconds(t + timedelta(days=5), t, actionable=True) == 432000


def test_discovery_requires_explicit_visible_basis_and_action_for_useful_lead():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    solicitation = t + timedelta(days=5)
    event = EvidenceEvent("e1", "weather-source", t, t, t, t, {"weather": "clear"})
    scenario = Scenario("claim", "1", 3, (t,), (event,),
                        GroundTruth("episode-1", "OPEN", solicitation_at=solicitation))

    def score(forecast, action):
        ledger = FrozenDecisionLedger()
        ledger.append(FrozenDecision("claim", t, "policy", ("e1",), forecast, action))
        return evaluate_replay(scenario, ledger.records)

    correct = {"discovery": {"episode_id": "episode-1", "basis_evidence_ids": ["e1"]}}
    result = score(correct, "BID_REVIEW")
    assert result.discovery["precision"] == result.discovery["recall"] == 1.0
    assert result.procurement["useful_lead_seconds"] is None
    assert result.invariant_status == "PASS"

    ignored = score({}, "IGNORE")
    vague = score({"discovery": {"episode_id": "episode-1", "basis_evidence_ids": ["hidden"]}}, "RESEARCH")
    assert ignored.discovery["precision"] is None and ignored.discovery["recall"] == 0.0
    assert vague.discovery["precision"] is None and vague.discovery["recall"] == 0.0
    assert vague.procurement["useful_lead_seconds"] is None

    wrong = score({"discovery": {"episode_id": "other", "basis_evidence_ids": ["e1"]}}, "PREPARE")
    assert wrong.discovery["precision"] == 0.0 and wrong.discovery["recall"] == 0.0
    assert wrong.procurement["useful_lead_seconds"] is None

    watch = score(correct, "WATCH")
    assert watch.discovery["recall"] == 1.0
    assert watch.procurement["useful_lead_seconds"] is None
    assert watch.invariant_status == "PASS"


def test_useful_lead_requires_matching_reviewed_episode_evidence_and_frozen_action():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    solicitation = t + timedelta(days=5)
    attestation = ActionSupportAttestation("episode-1", "BID_REVIEW", "reviewer", t,
                                          "solicitation line", "Explicit bid deadline and scope")
    evidence = EvidenceEvent("e1", "source", t, t, t, t,
                             source_spans=("solicitation line",), action_support=attestation)
    scenario = Scenario("lead", "1", 1, (t,), (evidence,),
                        GroundTruth("episode-1", "OPEN", solicitation_at=solicitation))
    forecast = {"discovery": {"episode_id": "episode-1", "basis_evidence_ids": ["e1"]}}

    def score(*, time=t, decision_scenario="lead", visible=("e1",), claim=forecast,
              action="BID_REVIEW", review=attestation, evidence_id="e1", corrupt=False):
        event = replace(evidence, action_support=review)
        candidate = replace(scenario, evidence=(replace(event, evidence_id=evidence_id),))
        ledger = FrozenDecisionLedger()
        record = ledger.append(FrozenDecision(decision_scenario, time, "policy", visible, claim, action))
        if corrupt:
            record = replace(record, action="PREPARE")
            decisions = (record,)
        else:
            decisions = ledger.records
        return evaluate_replay(candidate, decisions)

    assert score().procurement["useful_lead_seconds"] == 5 * 86400
    assert score(action="PREPARE").procurement["useful_lead_seconds"] is None
    assert score(action="RESEARCH").procurement["useful_lead_seconds"] is None
    assert score(time=t + timedelta(days=1), review=replace(attestation, reviewed_at=t + timedelta(days=2))).procurement[
        "useful_lead_seconds"] is None
    assert score(time=solicitation).procurement["useful_lead_seconds"] is None
    assert score(time=solicitation + timedelta(seconds=1)).procurement["useful_lead_seconds"] is None
    assert score(visible=()).procurement["useful_lead_seconds"] is None
    assert score(decision_scenario="other").procurement["useful_lead_seconds"] is None
    wrong_episode = replace(attestation, procurement_episode_id="other")
    assert score(review=wrong_episode).procurement["useful_lead_seconds"] is None
    unrelated = {"discovery": {"episode_id": "episode-1", "basis_evidence_ids": ["unrelated"]}}
    assert score(claim=unrelated).procurement["useful_lead_seconds"] is None
    absent_claim = {"discovery": {"episode_id": "episode-1", "basis_evidence_ids": ["absent-from-scenario"]}}
    assert score(claim=absent_claim, visible=("absent-from-scenario",)).procurement[
        "useful_lead_seconds"] is None
    for basis in (["e1", None], ["e1", "not-visible"]):
        mixed = {"discovery": {"episode_id": "episode-1", "basis_evidence_ids": basis}}
        result = score(claim=mixed, visible=("e1",))
        assert result.discovery["precision"] is None and result.discovery["recall"] == 0.0
        assert result.procurement["useful_lead_seconds"] is None
    assert score(corrupt=True).procurement["useful_lead_seconds"] is None


def test_useful_lead_uses_earliest_qualifying_decision():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    solicitation = t + timedelta(days=5)
    attestation = ActionSupportAttestation("episode-1", "PREPARE", "reviewer", t,
                                          "line 1", "Specific basis")
    event = EvidenceEvent("e1", "source", t, t, t, t, source_spans=("line 1",),
                          action_support=attestation)
    scenario = Scenario("earliest", "1", 1, (t,), (event,),
                        GroundTruth("episode-1", "OPEN", solicitation_at=solicitation))
    forecast = {"discovery": {"episode_id": "episode-1", "basis_evidence_ids": ["e1"]}}
    ledger = FrozenDecisionLedger()
    ledger.append(FrozenDecision("earliest", t + timedelta(days=2), "policy", ("e1",), forecast, "PREPARE"))
    ledger.append(FrozenDecision("earliest", t + timedelta(days=1), "policy", ("e1",), forecast, "PREPARE"))
    assert evaluate_replay(scenario, ledger.records).procurement["useful_lead_seconds"] == 4 * 86400


def test_repeated_episode_claims_do_not_inflate_discovery_precision():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    event = EvidenceEvent("e1", "s", t, t, t, t, {"signal": "visible"})
    scenario = Scenario("dedupe", "1", 1, (t,), (event,), GroundTruth("episode-1", "OPEN"))
    ledger = FrozenDecisionLedger()
    ledger.append(FrozenDecision("dedupe", t, "policy", ("e1",),
                                 {"discovery": {"episode_id": "wrong", "basis_evidence_ids": ["e1"]}},
                                 "WATCH"))
    for _ in range(9):
        ledger.append(FrozenDecision("dedupe", t, "policy", ("e1",),
                                     {"discovery": {"episode_id": "episode-1", "basis_evidence_ids": ["e1"]}},
                                     "WATCH"))
    result = evaluate_replay(scenario, ledger.records)
    assert result.discovery["precision"] == 0.5
    assert result.discovery["recall"] == 1.0
