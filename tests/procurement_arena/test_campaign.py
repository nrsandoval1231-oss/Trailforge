from athena_procurement_arena import BaselineA, keyword_rfp
from athena_procurement_arena.campaign import run_campaign, run_family_campaign


def test_campaign_is_seeded_and_compares_control_and_baseline():
    policies = {"KEYWORD": keyword_rfp, "BASELINE_A": BaselineA()}
    first = run_campaign(100, policies, seed=12)
    second = run_campaign(100, policies, seed=12)
    assert first["status"] == "PASS" and first["policies"]["BASELINE_A"]["runs"] == 100
    assert first["policies"] == second["policies"]
    assert first["policies"]["BASELINE_A"]["invariant_failures"] == 0

def test_all_family_templates_execute_for_both_policies():
    result = run_family_campaign({"KEYWORD": keyword_rfp, "BASELINE_A": BaselineA()}, seed=30)
    assert result["family_count"] == 40
    assert all(policy["runs"] == 40 and policy["invariant_failures"] == 0
               for policy in result["policies"].values())
