import athena_procurement_arena.campaign as campaign_module
from athena_procurement_arena import BaselineA, keyword_rfp
from athena_procurement_arena.campaign import (
    run_campaign,
    run_family_campaign,
    run_mutation_campaign,
    run_regression_campaign,
    synthetic_scenario,
)


def test_campaign_is_seeded_and_compares_control_and_baseline():
    policies = {"KEYWORD": keyword_rfp, "BASELINE_A": BaselineA()}
    first = run_campaign(100, policies, seed=12)
    second = run_campaign(100, policies, seed=12)
    assert first["status"] == "PASS" and first["policies"]["BASELINE_A"]["runs"] == 100
    assert first["policies"] == second["policies"]
    assert first["policies"]["BASELINE_A"]["invariant_failures"] == 0
    assert first["observability"]["executed_policy_runs"] == 200
    assert first["observability"]["failures"] == 0

def test_all_family_templates_execute_for_both_policies():
    result = run_family_campaign({"KEYWORD": keyword_rfp, "BASELINE_A": BaselineA()}, seed=30)
    assert result["family_count"] == 40
    assert all(policy["runs"] == 40 and policy["invariant_failures"] == 0
               for policy in result["policies"].values())

def test_regression_campaign_reports_separate_metrics():
    result = run_regression_campaign({"KEYWORD": keyword_rfp, "BASELINE_A": BaselineA()}, seed=30)
    baseline = result["policies"]["BASELINE_A"]
    assert baseline["runs"] == 40 and baseline["discovery_recall"] == 1.0
    assert baseline["power_evaluated_runs"] == 0


def test_regression_campaign_counts_ledger_invariant_failures(monkeypatch):
    real_world = campaign_module.TemporalWorld

    class FailingLedger:
        def __init__(self, ledger):
            self.records = ledger.records

        def verify(self):
            return False

    class FailingVerificationWorld:
        def __init__(self, *args, **kwargs):
            self._world = real_world(*args, **kwargs)

        def run(self):
            self._world.run()

        @property
        def ledger(self):
            return FailingLedger(self._world.ledger)

    monkeypatch.setattr(campaign_module, "TemporalWorld", FailingVerificationWorld)
    result = run_regression_campaign({"BASELINE_A": BaselineA()}, seed=30)
    assert result["policies"]["BASELINE_A"]["invariant_failures"] == 40
    assert result["status"] == "FAIL"


def test_all_campaign_modes_fail_when_ledger_verification_fails(monkeypatch):
    real_world = campaign_module.TemporalWorld

    class FailingLedger:
        def __init__(self, ledger):
            self.records = ledger.records

        def verify(self):
            return False

    class FailingWorld:
        def __init__(self, *args, **kwargs):
            self._world = real_world(*args, **kwargs)

        def run(self):
            return self._world.run()

        @property
        def ledger(self):
            return FailingLedger(self._world.ledger)

    monkeypatch.setattr(campaign_module, "TemporalWorld", FailingWorld)
    policies = {"BASELINE_A": BaselineA()}
    batch = run_campaign(1, policies)
    family = run_family_campaign(policies)
    regression = run_regression_campaign(policies)
    mutation = run_mutation_campaign(synthetic_scenario(1), 1, policies)
    assert batch["status"] == "FAIL" and batch["policies"]["BASELINE_A"]["invariant_failures"] == 1
    assert family["status"] == "FAIL" and family["policies"]["BASELINE_A"]["invariant_failures"] == 40
    assert regression["status"] == "FAIL" and regression["policies"]["BASELINE_A"]["invariant_failures"] == 40
    assert mutation["status"] == "FAIL" and mutation["policies"]["BASELINE_A"]["invariant_failures"] == 1


def test_one_thousand_mutation_variants_replay_without_invariant_failures():
    result = run_mutation_campaign(synthetic_scenario(9), 1000, {"BASELINE_A": BaselineA()}, seed=9)
    assert result["variant_count"] == 1000
    assert result["policies"]["BASELINE_A"]["invariant_failures"] == 0
