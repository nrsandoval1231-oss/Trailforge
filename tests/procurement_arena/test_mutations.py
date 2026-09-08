from athena_procurement_arena.campaign import synthetic_scenario
from athena_procurement_arena.mutations import mutate_scenarios


def test_mutations_are_seeded_and_preserve_truth():
    base = synthetic_scenario(10)
    first = mutate_scenarios(base, 5, seed=3)
    second = mutate_scenarios(base, 5, seed=3)
    assert [item[0].scenario_id for item in first] == [item[0].scenario_id for item in second]
    assert [item[1].parameters for item in first] == [item[1].parameters for item in second]
    assert all(item[0].truth == base.truth for item in first)
