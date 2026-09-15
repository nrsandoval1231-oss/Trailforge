from athena_procurement_arena.campaign import synthetic_scenario
from athena_procurement_arena.mutations import MUTATION_OPERATIONS, mutate_scenarios


def test_mutations_are_seeded_and_preserve_truth():
    base = synthetic_scenario(10)
    first = mutate_scenarios(base, 5, seed=3)
    second = mutate_scenarios(base, 5, seed=3)
    assert [item[0].scenario_id for item in first] == [item[0].scenario_id for item in second]
    assert [item[1].parameters for item in first] == [item[1].parameters for item in second]
    assert all(item[0].truth == base.truth for item in first)


def test_mutations_cover_packet_evidence_and_world_dimensions_without_changing_truth():
    base = synthetic_scenario(10)
    variants = mutate_scenarios(base, len(MUTATION_OPERATIONS), seed=9)
    assert tuple(record.operation for _, record in variants) == MUTATION_OPERATIONS
    assert all(scenario.truth == base.truth for scenario, _ in variants)
    assert all(scenario.evidence for scenario, _ in variants)
