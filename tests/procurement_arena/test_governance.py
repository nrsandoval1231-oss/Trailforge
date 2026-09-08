from athena_procurement_arena.governance import CandidateLesson, NegativeKnowledge, govern_candidate

def test_governance_never_self_promotes_without_holdout():
    result = govern_candidate("c1", {"recall": .5}, {"recall": .9}, invariant_failures=0,
                              adversarial_pass=True, counterfactual_pass=True)
    assert result.outcome == "QUARANTINE"

def test_negative_knowledge_persists_rejected_lessons():
    store = NegativeKnowledge()
    lesson = CandidateLesson("l1", "x", ("s1",), (), "BASELINE_A", {"threshold": 2}, {"recall": .1})
    store.reject(lesson)
    assert store.contains("l1") and store.lessons == (lesson,)
