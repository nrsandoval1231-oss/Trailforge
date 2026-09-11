import json
from dataclasses import replace
from pathlib import Path

import pytest

from athena_procurement_arena import (
    content_fingerprint,
    current_target_fixtures,
    load_bundle_mapping,
    score_fixture_bundle,
    split_fixture_ids,
)
from athena_procurement_arena.campaign import synthetic_scenario
from athena_procurement_arena.foundation import GroundTruth
from athena_procurement_arena.policies import BaselineA, classify_scope
from athena_procurement_arena.scenario_dsl import ScenarioDsl
from athena_procurement_arena.scenarios import family_scenario


def _fixture(fixture_id="f1", status="VERIFIED"):
    return {
        "fixture_id": fixture_id,
        "status": status,
        "source_url": "https://example.com/source/1",
        "source_sha256": "a" * 64,
        "retrieved_at": "2026-09-08T12:00:00+00:00",
        "verified_by": "human-reviewer",
        "verification_notes": "Source and timeline manually checked.",
        "scenario": json.loads(ScenarioDsl.dumps(synthetic_scenario(1))),
    }


def test_current_target_shortlist_requires_lifecycle_and_prime_power_gates():
    qualified = _fixture("open", "VERIFIED")
    qualified["opportunity_status"] = "OPEN"
    scenario = family_scenario("public_rfp", 4)
    scenario = replace(scenario, evidence=tuple(
        replace(item, claims={
            key: value for key, value in item.claims.items() if key != "signal"
        } | {
            "commissioning_scope": "planned temporary power",
            "required_kw": 300,
            "primary_fuel": "propane",
        })
        for item in scenario.evidence
    ))
    qualified["scenario"] = json.loads(ScenarioDsl.dumps(scenario))
    closed = dict(qualified)
    closed["fixture_id"] = "closed"
    closed["opportunity_status"] = "CLOSED"
    unknown = _fixture("unknown", "VERIFIED")
    bundle = load_bundle_mapping({
        "schema_version": "procurement-arena-fixture-bundle-v1",
        "bundle_id": "b4",
        "version": "1",
        "fixtures": [qualified, closed, unknown],
    })
    assert tuple(item.fixture_id for item in current_target_fixtures(bundle)) == ("open",)


def test_verified_bundle_round_trips_and_holdout_is_fail_closed():
    raw = {"schema_version": "procurement-arena-fixture-bundle-v1", "bundle_id": "b1", "version": "1",
           "fixtures": [_fixture()], "holdout_fixture_ids": []}
    bundle = load_bundle_mapping(raw)
    assert bundle.sealed_holdout_available is False
    assert bundle.fixtures[0].scoreable is False
    assert load_bundle_mapping(json.loads(bundle.dumps())).as_dict() == bundle.as_dict()


def test_sealed_holdout_requires_sealed_ready_fixture():
    with pytest.raises(ValueError, match="SEALED_READY"):
        load_bundle_mapping({"schema_version": "procurement-arena-fixture-bundle-v1", "bundle_id": "b1",
                             "version": "1", "fixtures": [_fixture()], "holdout_fixture_ids": ["f1"]})


def test_provenance_and_digest_validation_fail_closed():
    item = _fixture()
    item["source_sha256"] = "not-a-digest"
    with pytest.raises(ValueError, match="64-character"):
        load_bundle_mapping({"schema_version": "procurement-arena-fixture-bundle-v1", "bundle_id": "b1",
                             "version": "1", "fixtures": [item]})
    assert content_fingerprint("x") == "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881"


def test_split_is_seeded_and_does_not_claim_verification():
    ids = tuple(f"f{i}" for i in range(10))
    assert split_fixture_ids(ids, seed=9) == split_fixture_ids(ids, seed=9)
    train, holdout = split_fixture_ids(ids, seed=9)
    assert set(train).isdisjoint(holdout) and set(train) | set(holdout) == set(ids)


def test_sealed_holdout_scores_exact_outcome_and_unsealed_fails_closed():
    scenario = replace(synthetic_scenario(3), truth=GroundTruth("p-3", "SOLICITATION_RELEASED"))
    item = _fixture("holdout", "SEALED_READY")
    item["scenario"] = json.loads(ScenarioDsl.dumps(scenario))
    bundle = load_bundle_mapping({"schema_version": "procurement-arena-fixture-bundle-v1", "bundle_id": "b1",
                                  "version": "1", "fixtures": [item], "holdout_fixture_ids": ["holdout"]})
    result = score_fixture_bundle("BASELINE_A", BaselineA(), bundle)
    assert result["accuracy"] == 1.0 and result["correct"] == 1
    unsealed = load_bundle_mapping({"schema_version": "procurement-arena-fixture-bundle-v1", "bundle_id": "b2",
                                    "version": "1", "fixtures": [_fixture()], "holdout_fixture_ids": []})
    with pytest.raises(ValueError, match="sealed holdout"):
        score_fixture_bundle("BASELINE_A", BaselineA(), unsealed)


def test_source_backed_target_fixtures_are_in_scope_and_not_sealed():
    for path in ("gt-007-pleasanton.json", "gt-008-mobile.json"):
        bundle = load_bundle_mapping(json.loads(
            Path(f"scenarios/fixtures/verified/{path}").read_text(encoding="utf-8")))
        evidence = bundle.fixtures[0].scenario.evidence
        assert classify_scope(evidence) == "IN_SCOPE_INSTALLATION_OR_TEMPORARY_POWER"
        assert bundle.fixtures[0].status == "VERIFIED"
        assert bundle.sealed_holdout_available is False
        assert bundle.fixtures[0].current is False


def test_unknown_lifecycle_status_fails_closed_for_current_leads():
    bundle = load_bundle_mapping({"schema_version": "procurement-arena-fixture-bundle-v1", "bundle_id": "b3",
                                  "version": "1", "fixtures": [_fixture()], "holdout_fixture_ids": []})
    assert bundle.fixtures[0].opportunity_status == "UNKNOWN"
    assert bundle.fixtures[0].current is False


def test_source_backed_morgan_hill_fixture_is_verified_but_not_sealed():
    bundle = load_bundle_mapping(json.loads(
        Path("scenarios/fixtures/verified/gt-003-morgan-hill.json").read_text(encoding="utf-8")))
    assert bundle.fixtures[0].status == "VERIFIED"
    assert bundle.sealed_holdout_available is False
    assert bundle.fixtures[0].scenario.truth.outcome == "SOLICITATION_RELEASED"
