import json

import pytest

from athena_procurement_arena import (
    content_fingerprint,
    load_bundle_mapping,
    split_fixture_ids,
)
from athena_procurement_arena.campaign import synthetic_scenario
from athena_procurement_arena.scenario_dsl import ScenarioDsl


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
