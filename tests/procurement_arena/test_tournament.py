from athena_procurement_arena.foundation import validate_scenario
from athena_procurement_arena.scenarios import (
    SCENARIO_FAMILIES,
    family_scenario,
    validate_family_registry,
)
from athena_procurement_arena.tournament import tournament_decision


def test_registry_has_all_forty_declared_families():
    assert len(validate_family_registry()) == 40 and len(SCENARIO_FAMILIES) == 40
    assert all(validate_scenario(family_scenario(name, 4)) for name in SCENARIO_FAMILIES)

def test_tournament_rejects_weak_candidate_and_promotes_pareto_winner():
    weak = tournament_decision("weak", {"recall": .2, "precision": .2}, {"recall": .5, "precision": .5})
    strong = tournament_decision("strong", {"recall": .8, "precision": .7, "cost": 1},
                                 {"recall": .5, "precision": .5, "cost": 2})
    assert weak["outcome"] == "REJECT" and strong["outcome"] == "PROMOTE"
