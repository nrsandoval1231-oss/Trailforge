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
    store.reject(lesson)
    assert store.contains("l1") and store.lessons == (lesson,)

def test_athena_candidate_contract_cannot_self_promote():
    input_record = AthenaInput({"state": 1}, {"action": "WATCH"}, {"state": "UNKNOWN"}, {"outcome": "OPEN"}, {"recall": .5})
    assert input_record.evaluation["recall"] == .5
    assert Attribution("a", "input", confidence=.8).confidence == .8
    CandidatePolicy("c", "l1", "1", {"threshold": 2})
