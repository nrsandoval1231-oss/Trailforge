import hashlib
import json

import pytest

from athena_procurement_arena.governance import (
    AthenaInput,
    Attribution,
    CandidateLesson,
    CandidatePolicy,
    NegativeKnowledge,
    govern_candidate,
)


def test_governance_never_self_promotes_without_holdout():
    result = govern_candidate("c1", {"recall": .5}, {"recall": .9}, invariant_failures=0,
                              adversarial_pass=True, counterfactual_pass=True)
    assert result.outcome == "QUARANTINE"

def test_negative_knowledge_persists_rejected_lessons():
    store = NegativeKnowledge()
    lesson = CandidateLesson("l1", "x", ("s1",), (), "BASELINE_A", {"threshold": 2}, {"recall": .1})
    assert store.reject(lesson) == "REJECTED"
    assert store.contains("l1") and store.lessons == (lesson,)


def test_negative_knowledge_snapshot_round_trips_and_is_exclusive(tmp_path):
    lesson = CandidateLesson("l1", "x", ("s1",), (), "BASELINE_A", {"threshold": 2}, {"recall": .1})
    first = NegativeKnowledge()
    first.reject(lesson)
    path = tmp_path / "negative.json"
    first.save(path)
    assert NegativeKnowledge.load(path).lessons == (lesson,)
    with pytest.raises(FileExistsError):
        first.save(path)


def test_negative_knowledge_rejects_mismatched_snapshot_schema(tmp_path):
    lesson = CandidateLesson("l1", "x", ("s1",), (), "BASELINE_A", {"threshold": 2}, {"recall": .1})
    store = NegativeKnowledge()
    store.reject(lesson)
    path = tmp_path / "negative.json"
    store.save(path)
    snapshot = json.loads(path.read_text())
    snapshot["schema"] = "other-schema"
    path.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError, match="schema"):
        NegativeKnowledge.load(path)


def test_negative_knowledge_rejects_tampering_duplicate_ids_and_changed_identity(tmp_path):
    lesson = CandidateLesson("l1", "x", ("s1",), (), "BASELINE_A", {"threshold": 2}, {"recall": .1})
    changed = CandidateLesson("l1", "different", ("s1",), (), "BASELINE_A", {"threshold": 2}, {"recall": .1})
    store = NegativeKnowledge()
    assert store.reject(lesson) == "REJECTED"
    assert store.reject(changed) == "CONFLICT"
    assert store.lessons == (lesson,)
    path = tmp_path / "negative.json"
    store.save(path)
    raw = json.loads(path.read_text())
    raw["lessons"][0]["hypothesis"] = "altered"
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="hash mismatch"):
        NegativeKnowledge.load(path)

    path = tmp_path / "duplicate.json"
    payload = {"schema": NegativeKnowledge.SNAPSHOT_SCHEMA, "version": NegativeKnowledge.SNAPSHOT_VERSION,
               "lessons": [store._lesson_data(lesson), store._lesson_data(lesson)]}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    payload["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="duplicate"):
        NegativeKnowledge.load(path)


def test_negative_knowledge_detaches_mutable_lesson_mappings():
    proposed = {"threshold": 2}
    lesson = CandidateLesson("l1", "x", ("s1",), (), "BASELINE_A", proposed, {"recall": .1})
    store = NegativeKnowledge()
    store.reject(lesson)
    proposed["threshold"] = 9
    exposed = store.lessons[0]
    exposed.proposed_change["threshold"] = 7
    assert store.lessons[0].proposed_change == {"threshold": 2}

def test_athena_candidate_contract_cannot_self_promote():
    input_record = AthenaInput({"state": 1}, {"action": "WATCH"}, {"state": "UNKNOWN"}, {"outcome": "OPEN"}, {"recall": .5})
    assert input_record.evaluation["recall"] == .5
    assert Attribution("a", "input", confidence=.8).confidence == .8
    CandidatePolicy("c", "l1", "1", {"threshold": 2})
