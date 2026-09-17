from datetime import UTC, datetime
from pathlib import Path

import pytest

from athena_procurement_arena import (
    BaselineA,
    ProspectiveCohort,
    ProspectiveOutcomeSeal,
    capture_prospective_shadow,
    evaluate_cohort,
    evaluate_prediction,
    load_cohort,
    load_seal,
    seal_prospective_outcome,
    write_cohort,
    write_seal,
)
from athena_procurement_arena.campaign import synthetic_scenario


def _shadow(record_id="shadow-1", outcome=None):
    return capture_prospective_shadow(
        record_id=record_id,
        captured_at=datetime(2026, 9, 14, tzinfo=UTC),
        source_url="https://example.com/record",
        source_sha256="a" * 64,
        verified_by="human-reviewer",
        scenario=synthetic_scenario(8),
        policy_id="BASELINE_A",
        policy=BaselineA(),
        known_outcome=outcome,
    )


def test_prediction_evaluation_is_exact_match():
    assert evaluate_prediction("SOLICITATION_RELEASED", "SOLICITATION_RELEASED") == {
        "predicted": "SOLICITATION_RELEASED",
        "actual": "SOLICITATION_RELEASED",
        "correct": True,
    }
    assert evaluate_prediction("SOLICITATION_RELEASED", "AWARDED")["correct"] is False


def test_seal_binds_shadow_to_outcome_and_preserves_absent_authority():
    shadow = _shadow()
    predicted = shadow.manifest["metrics"]["final_procurement_state"]
    seal = seal_prospective_outcome(
        shadow,
        seal_id="seal-1",
        verified_outcome=predicted,
        verified_at=datetime(2026, 9, 20, tzinfo=UTC),
        verified_by="outcome-reviewer",
    )
    assert isinstance(seal, ProspectiveOutcomeSeal)
    assert seal.execution_authority == "ABSENT"
    assert seal.evaluation["predicted"] == seal.evaluation["actual"]
    assert seal.evaluation["correct"] is True
    assert seal.seal_hash == seal_prospective_outcome(
        shadow,
        seal_id="seal-1",
        verified_outcome=predicted,
        verified_at=datetime(2026, 9, 20, tzinfo=UTC),
        verified_by="outcome-reviewer",
    ).seal_hash


def test_seal_rejects_non_absent_authority_and_missing_fields():
    shadow = _shadow()
    with pytest.raises(ValueError, match="verified_outcome"):
        seal_prospective_outcome(
            shadow,
            seal_id="seal-1",
            verified_outcome="",
            verified_at=datetime(2026, 9, 20, tzinfo=UTC),
            verified_by="reviewer",
        )
    with pytest.raises(ValueError, match="verified_by"):
        seal_prospective_outcome(
            shadow,
            seal_id="seal-1",
            verified_outcome="AWARDED",
            verified_at=datetime(2026, 9, 20, tzinfo=UTC),
            verified_by="",
        )


def test_cohort_aggregates_and_applies_governance_floor():
    shadows = [
        _shadow("s1"),
        _shadow("s2"),
        _shadow("s3"),
    ]
    predicted = shadows[0].manifest["metrics"]["final_procurement_state"]
    wrong = "AWARDED" if predicted != "AWARDED" else "SOLICITATION_RELEASED"
    seals = (
        seal_prospective_outcome(
            shadows[0], seal_id="seal-1", verified_outcome=predicted,
            verified_at=datetime(2026, 9, 20, tzinfo=UTC), verified_by="r",
        ),
        seal_prospective_outcome(
            shadows[1], seal_id="seal-2", verified_outcome=predicted,
            verified_at=datetime(2026, 9, 20, tzinfo=UTC), verified_by="r",
        ),
        seal_prospective_outcome(
            shadows[2], seal_id="seal-3", verified_outcome=wrong,
            verified_at=datetime(2026, 9, 20, tzinfo=UTC), verified_by="r",
        ),
    )
    cohort = evaluate_cohort(
        "cohort-1",
        seals,
        floors={"accuracy": 0.5},
        incumbent_metrics={"accuracy": 0.5, "incorrect": 2},
    )
    assert isinstance(cohort, ProspectiveCohort)
    assert cohort.metrics["seals"] == 3
    assert cohort.metrics["correct"] == 2
    assert cohort.metrics["accuracy"] == pytest.approx(2 / 3)
    assert cohort.governance["meets_floors"] is True
    assert cohort.governance["pareto_dominates"] is True


def test_cohort_requires_non_empty_seal_set():
    with pytest.raises(ValueError, match="at least one seal"):
        evaluate_cohort("empty", ())


def test_cohort_rejects_duplicate_seal_ids():
    shadow = _shadow()
    seal = seal_prospective_outcome(
        shadow, seal_id="dup", verified_outcome="AWARDED",
        verified_at=datetime(2026, 9, 20, tzinfo=UTC), verified_by="r",
    )
    with pytest.raises(ValueError, match="unique"):
        ProspectiveCohort("bad", (seal, seal), {"a": 1}, {"b": True})


def test_seal_round_trips_through_json(tmp_path: Path):
    shadow = _shadow()
    seal = seal_prospective_outcome(
        shadow,
        seal_id="seal-rt",
        verified_outcome="SOLICITATION_RELEASED",
        verified_at=datetime(2026, 9, 20, tzinfo=UTC),
        verified_by="outcome-reviewer",
    )
    path = write_seal(seal, tmp_path / "seal.json")
    loaded = load_seal(path)
    assert loaded.seal_hash == seal.seal_hash
    assert loaded.shadow_record.record_hash == seal.shadow_record.record_hash


def test_cohort_round_trips_through_json(tmp_path: Path):
    shadow = _shadow()
    seal = seal_prospective_outcome(
        shadow,
        seal_id="seal-rt",
        verified_outcome="SOLICITATION_RELEASED",
        verified_at=datetime(2026, 9, 20, tzinfo=UTC),
        verified_by="outcome-reviewer",
    )
    cohort = evaluate_cohort("cohort-rt", (seal,))
    path = write_cohort(cohort, tmp_path / "cohort.json")
    loaded = load_cohort(path)
    assert loaded.cohort_id == cohort.cohort_id
    assert loaded.metrics == cohort.metrics
    assert len(loaded.seals) == 1
    assert loaded.seals[0].seal_hash == seal.seal_hash


def test_seal_load_rejects_bad_schema(tmp_path: Path):
    path = tmp_path / "bad-seal.json"
    path.write_text("""{"schema_version": "other"}""", encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        load_seal(path)


def test_cohort_load_rejects_bad_schema(tmp_path: Path):
    path = tmp_path / "bad-cohort.json"
    path.write_text("""{"schema_version": "other"}""", encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        load_cohort(path)
