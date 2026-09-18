from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from athena_procurement_arena.cli import main
from athena_procurement_arena.rfp_candidate_capture import candidate_from_excerpt, write_rfp_candidate
from athena_procurement_arena.rfp_candidate_queue import (
    RfpCandidateQueue,
    RfpCandidateQueueRecord,
    build_rfp_candidate_queue,
    write_rfp_candidate_queue,
)


def _write_candidate(tmp_path, candidate_id: str, excerpt: str = "Buyer needs 500 kW prime power."):
    path = tmp_path / f"{candidate_id}.json"
    candidate = candidate_from_excerpt(
        excerpt=excerpt, candidate_id=candidate_id, source_url=f"https://example.com/{candidate_id}",
        source_quote="500 kW prime power", buyer="Example Buyer", scope="temporary prime power",
        published_at=datetime(2026, 9, 1, tzinfo=UTC), retrieved_at=datetime(2026, 9, 2, tzinfo=UTC),
        captured_by="operator", required_kw=500,
    )
    write_rfp_candidate(candidate, path)
    return path, candidate


def test_queue_is_stable_pending_only_and_contains_no_excerpt(tmp_path) -> None:
    first_path, first = _write_candidate(tmp_path, "rfp-001")
    second_path, second = _write_candidate(tmp_path, "rfp-002")
    assembled_at = datetime(2026, 9, 3, tzinfo=UTC)
    queue = build_rfp_candidate_queue(
        [str(first_path), str(second_path)], queue_id="queue-001",
        assembled_by="review-coordinator", assembled_at=assembled_at,
    )
    rebuilt = build_rfp_candidate_queue(
        [str(first_path), str(second_path)], queue_id="queue-001",
        assembled_by="review-coordinator", assembled_at=assembled_at,
    )
    assert queue.queue_hash == rebuilt.queue_hash
    assert [record.candidate_hash for record in queue.records] == [first.candidate_hash, second.candidate_hash]
    assert {record.review_status for record in queue.records} == {"PENDING_REVIEW"}

    output = tmp_path / "queue.json"
    write_rfp_candidate_queue(queue, output)
    text = output.read_text(encoding="utf-8")
    assert "Buyer needs 500 kW prime power." not in text
    assert "source_quote" not in text
    assert json.loads(text)["queue_hash"] == queue.queue_hash
    with pytest.raises(FileExistsError, match="overwrite"):
        write_rfp_candidate_queue(queue, output)


def test_queue_rejects_duplicate_ids_and_invalid_candidates(tmp_path) -> None:
    first_path, _ = _write_candidate(tmp_path, "rfp-001")
    duplicate_path = tmp_path / "duplicate.json"
    duplicate_path.write_text(first_path.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate candidate IDs"):
        build_rfp_candidate_queue(
            [str(first_path), str(duplicate_path)], queue_id="queue-001",
            assembled_by="reviewer", assembled_at=datetime(2026, 9, 3, tzinfo=UTC),
        )

    tampered = json.loads(first_path.read_text(encoding="utf-8"))
    tampered["buyer"] = "Changed Buyer"
    first_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        build_rfp_candidate_queue(
            [str(first_path)], queue_id="queue-001", assembled_by="reviewer",
            assembled_at=datetime(2026, 9, 3, tzinfo=UTC),
        )


def test_queue_requires_timezone_aware_assembly_time(tmp_path) -> None:
    candidate_path, _ = _write_candidate(tmp_path, "rfp-001")
    with pytest.raises(ValueError, match="timezone-aware"):
        build_rfp_candidate_queue(
            [str(candidate_path)], queue_id="queue-001", assembled_by="reviewer",
            assembled_at=datetime(2026, 9, 3),
        )


def test_queue_records_are_immutable_and_reject_non_pending_state() -> None:
    record = RfpCandidateQueueRecord("candidate.json", "rfp-001", "a" * 64)
    with pytest.raises(FrozenInstanceError):
        record.review_status = "ACCEPTED"
    with pytest.raises(ValueError, match="PENDING_REVIEW"):
        RfpCandidateQueueRecord(
            "candidate.json", "rfp-001", "a" * 64, review_status="ACCEPTED"
        ).as_dict()


def test_queue_rejects_extra_raw_fields_and_revalidates_before_serialization(tmp_path) -> None:
    with pytest.raises(TypeError):
        RfpCandidateQueueRecord(
            path="candidate.json", candidate_id="rfp-001", candidate_hash="a" * 64,
            raw_excerpt="raw source text",
        )
    with pytest.raises(TypeError):
        RfpCandidateQueueRecord(
            path="candidate.json", candidate_id="rfp-001", candidate_hash="a" * 64,
            source_quote="exact quote",
        )
    with pytest.raises(ValueError, match="immutable allowlisted"):
        RfpCandidateQueue(
            "queue-001", "reviewer", datetime(2026, 9, 3, tzinfo=UTC),
            ({"path": "candidate.json", "candidate_id": "rfp-001", "candidate_hash": "a" * 64,
              "review_status": "PENDING_REVIEW", "raw_excerpt": "raw source text"},),
        )

    record = RfpCandidateQueueRecord("candidate.json", "rfp-001", "a" * 64)
    queue = RfpCandidateQueue(
        "queue-001", "reviewer", datetime(2026, 9, 3, tzinfo=UTC), (record,),
    )
    object.__setattr__(record, "review_status", "ACCEPTED")
    with pytest.raises(ValueError, match="PENDING_REVIEW"):
        write_rfp_candidate_queue(queue, tmp_path / "queue.json")


def test_cli_builds_review_queue(tmp_path, capsys) -> None:
    candidate_path, candidate = _write_candidate(tmp_path, "rfp-001")
    output = tmp_path / "queue.json"
    assert main([
        "build-rfp-review-queue", "--candidates", str(candidate_path), "--queue-id", "queue-001",
        "--assembled-by", "review-coordinator", "--assembled-at", "2026-09-03T00:00:00+00:00",
        "--output", str(output),
    ]) == 0
    emitted = json.loads(capsys.readouterr().out)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert emitted["candidate_count"] == 1
    assert emitted["queue_hash"] == payload["queue_hash"]
    assert payload["records"] == [{
        "candidate_hash": candidate.candidate_hash,
        "candidate_id": "rfp-001",
        "path": str(candidate_path),
        "review_status": "PENDING_REVIEW",
    }]
