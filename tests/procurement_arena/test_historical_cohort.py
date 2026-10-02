import json
from datetime import UTC, datetime
from hashlib import sha256

import pytest

from athena_procurement_arena.historical_cohort import build_historical_report
from athena_procurement_arena.public_capture import capture_markdown, write_capture


def _base(tmp_path, *, identity="RESOLVED"):
    original_url = "https://example.org/announcement"
    content = "Project announcement\nPublished: 2025-01-01\nMilestone: 2025-02-01\n"
    capture = capture_markdown(original_url, content, capture_id="source", captured_by="operator")
    if not (tmp_path / "source.json").exists():
        write_capture(capture, tmp_path / "source.json")
    signals = [
        {"signal_id": "early", "signal_type": "PROJECT_ANNOUNCED", "title": "Announcement", "source_url": original_url,
         "source_capture_path": "source.json", "excerpt": "Project announcement", "source_sha256": sha256(content.encode()).hexdigest(),
         "published_at": "2025-01-01", "published_date_precision": "day", "published_date_excerpt": "Published: 2025-01-01",
         "published_date_basis": "DISPLAYED_SOURCE_DATE_NOT_VERIFIED_AVAILABILITY", "available_at": None},
        {"signal_id": "target", "signal_type": "POWER_REQUIREMENT", "title": "Requirement", "source_url": original_url,
         "source_capture_path": "source.json", "excerpt": "Milestone: 2025-02-01", "source_sha256": sha256(content.encode()).hexdigest(),
         "published_at": "2025-02-01", "published_date_precision": "day", "published_date_excerpt": "Milestone: 2025-02-01",
         "published_date_basis": "DISPLAYED_SOURCE_DATE_NOT_VERIFIED_AVAILABILITY", "available_at": None},
    ]
    return {"schema_version": "trailforge-historical-cohort-input-v1", "cohort_id": "test-cohort",
            "policy": {"target_signal_type": "POWER_REQUIREMENT", "early_signal_types": ["PROJECT_ANNOUNCED"], "selection_basis": "predeclared policy"},
            "projects": [{"project_id": "project-a", "identity_status": identity, "identity_basis": "named source", "signals": signals,
                          "conventional_milestone_signal_id": "target", "buyer_path": {"organization": "Example", "status": "owner",
                          "evidence_capture_path": "source.json", "excerpt": "Project announcement", "available_at": None}}]}


def _write_input(tmp_path, data):
    path = tmp_path / "input.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _archive_signal(tmp_path, item, timestamp="20250202120000", captured_at=None):
    url = f"https://web.archive.org/web/{timestamp}/{item['source_url']}"
    archive_content = f"Archive capture timestamp {timestamp}. {item['excerpt']}"
    capture = capture_markdown(url, archive_content, capture_id=f"archive-{item['signal_id']}", captured_by="operator", captured_at=captured_at)
    filename = f"{item['signal_id']}-archive.json"
    write_capture(capture, tmp_path / filename)
    item.update({"available_at": f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}T{timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:14]}Z",
                 "availability_basis": "ARCHIVED_CONTENT", "availability_capture_path": filename,
                 "availability_excerpt": item["excerpt"], "availability_time_excerpt": timestamp})


def test_archive_timestamp_is_the_only_replay_availability(tmp_path):
    data = _base(tmp_path)
    early = data["projects"][0]["signals"][0]
    _archive_signal(tmp_path, early)
    source = _write_input(tmp_path, data)
    report = build_historical_report(source, tmp_path / "out")
    case = report["cases"][0]
    assert case["signals"][0]["availability_status"] == "SUPPORTED"
    assert case["signals"][1]["availability_status"] == "UNKNOWN"
    assert case["first_valid_policy_surface_status"] == "UNKNOWN"
    assert report["eligible_trace_count"] == 1
    assert report["replay"]["target_cases"] == 0
    assert case["signals"][0]["diagnostic_timezone_status"] == "UNKNOWN"
    assert (tmp_path / "out" / "report.md").exists()


def test_unresolved_identity_is_retained_but_never_replayed(tmp_path):
    data = _base(tmp_path, identity="UNRESOLVED")
    _archive_signal(tmp_path, data["projects"][0]["signals"][0])
    report = build_historical_report(_write_input(tmp_path, data), tmp_path / "out")
    assert report["project_count"] == 1
    assert report["eligible_trace_count"] == 0
    assert report["replay"] is None
    assert report["cases"][0]["signals"][0]["availability_status"] == "UNKNOWN"


def test_same_time_early_signal_is_not_a_lead(tmp_path):
    data = _base(tmp_path)
    _archive_signal(tmp_path, data["projects"][0]["signals"][0])
    _archive_signal(tmp_path, data["projects"][0]["signals"][1])
    # Both archive captures share the same timestamp, so no strict-before surface exists.
    report = build_historical_report(_write_input(tmp_path, data), tmp_path / "out")
    assert report["cases"][0]["conventional_milestone_status"] == "SUPPORTED"
    assert report["cases"][0]["first_valid_policy_surface_status"] == "UNKNOWN"
    assert report["replay"]["unresolved_without_early_signal"] == 1


def test_source_hash_mismatch_rejected(tmp_path):
    data = _base(tmp_path)
    data["projects"][0]["signals"][0]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source_sha256"):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")


def test_missing_evidence_and_invalid_signal_type_rejected(tmp_path):
    data = _base(tmp_path)
    data["projects"][0]["signals"][0]["excerpt"] = None
    with pytest.raises(ValueError, match="exact evidence excerpt"):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")
    data = _base(tmp_path)
    data["projects"][0]["signals"][0]["signal_type"] = "MADE_UP"
    with pytest.raises(ValueError):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")


def test_missing_published_date_quote_and_bad_archive_binding_rejected(tmp_path):
    data = _base(tmp_path)
    data["projects"][0]["signals"][0]["published_date_excerpt"] = "absent"
    with pytest.raises(ValueError, match="exact excerpt"):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")
    data = _base(tmp_path)
    early = data["projects"][0]["signals"][0]
    _archive_signal(tmp_path, early)
    early["available_at"] = "2025-01-01T11:59:59Z"
    with pytest.raises(ValueError, match="must equal the timestamp"):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")


def test_archive_host_and_official_capture_url_are_bound(tmp_path):
    data = _base(tmp_path)
    early = data["projects"][0]["signals"][0]
    _archive_signal(tmp_path, early)
    archive_path = tmp_path / early["availability_capture_path"]
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    archive["source_url"] = archive["source_url"].replace("web.archive.org", "example.com")
    # Recreate valid capture hash for an attacker-controlled lookalike URL.
    capture = capture_markdown(archive["source_url"], archive["content"], capture_id="fake-archive", captured_by="operator")
    write_capture(capture, tmp_path / "fake-archive.json")
    early["availability_capture_path"] = "fake-archive.json"
    with pytest.raises(ValueError, match="requires a web.archive.org"):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")

    data = _base(tmp_path)
    early = data["projects"][0]["signals"][0]
    stamp_text = "Official publication: 2025-02-02T12:00:00Z"
    capture = capture_markdown("https://example.org/different", f"{stamp_text} Project announcement", capture_id="official", captured_by="operator")
    write_capture(capture, tmp_path / "official.json")
    early.update({"available_at": "2025-02-02T12:00:00Z", "availability_basis": "OFFICIAL_PUBLICATION_TIMESTAMP",
                  "availability_capture_path": "official.json", "availability_excerpt": "Project announcement",
                  "availability_time_excerpt": "2025-02-02T12:00:00Z"})
    with pytest.raises(ValueError, match="must match the cited source URL"):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")


def test_future_archive_official_time_and_capture_are_rejected(tmp_path):
    data = _base(tmp_path)
    early = data["projects"][0]["signals"][0]
    _archive_signal(tmp_path, early, timestamp="20300101120000", captured_at=datetime(2030, 1, 1, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="availability capture postdates current run"):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")

    data = _base(tmp_path)
    early = data["projects"][0]["signals"][0]
    official_url = "https://example.org/announcement"
    official_time = "2030-01-01T12:00:00Z"
    content = f"Official publication: {official_time}. Project announcement"
    capture = capture_markdown(official_url, content, capture_id="future-official", captured_by="operator")
    write_capture(capture, tmp_path / "official.json")
    early.update({"available_at": official_time, "availability_basis": "OFFICIAL_PUBLICATION_TIMESTAMP",
                  "availability_capture_path": "official.json", "availability_excerpt": "Project announcement",
                  "availability_time_excerpt": official_time})
    with pytest.raises(ValueError, match="postdates a cited evidence capture"):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")

    data = _base(tmp_path)
    buyer = data["projects"][0]["buyer_path"]
    official_time = "2030-01-01T12:00:00Z"
    content = f"Official publication: {official_time}. Project announcement"
    capture = capture_markdown("https://example.org/announcement", content, capture_id="future-buyer", captured_by="operator")
    write_capture(capture, tmp_path / "buyer-time.json")
    buyer.update({"available_at": official_time, "availability_basis": "OFFICIAL_PUBLICATION_TIMESTAMP",
                  "availability_capture_path": "buyer-time.json", "availability_excerpt": "Project announcement",
                  "availability_time_excerpt": official_time})
    with pytest.raises(ValueError, match="postdates a cited evidence capture"):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")


def test_availability_equal_to_capture_boundary_is_valid(tmp_path):
    data = _base(tmp_path)
    early = data["projects"][0]["signals"][0]
    boundary = datetime(2025, 2, 2, 12, tzinfo=UTC)
    _archive_signal(tmp_path, early, captured_at=boundary)
    report = build_historical_report(_write_input(tmp_path, data), tmp_path / "out")
    assert report["cases"][0]["signals"][0]["availability_status"] == "SUPPORTED"


def test_buyer_identity_citation_retained_but_availability_unknown(tmp_path):
    data = _base(tmp_path)
    early, target = data["projects"][0]["signals"]
    _archive_signal(tmp_path, early)
    _archive_signal(tmp_path, target, timestamp="20250203120000")
    buyer = data["projects"][0]["buyer_path"]
    buyer["available_at"] = "2025-02-02T11:00:00Z"
    report = build_historical_report(_write_input(tmp_path, data), tmp_path / "out")
    path = report["cases"][0]["buyer_path"]
    assert path["status"] == "UNKNOWN"
    assert report["cases"][0]["first_valid_policy_surface_status"] == "SUPPORTED"
    assert path["stated_organization"] == "Example"
    assert path["organization"] is None


def test_unknown_milestone_rejected_and_output_must_be_empty(tmp_path):
    data = _base(tmp_path)
    data["projects"][0]["conventional_milestone_signal_id"] = "missing"
    with pytest.raises(ValueError, match="must reference"):
        build_historical_report(_write_input(tmp_path, data), tmp_path / "out")
    data = _base(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    (out / "prior.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError, match="new and empty"):
        build_historical_report(_write_input(tmp_path, data), out)
