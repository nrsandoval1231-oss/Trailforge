import copy
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from athena_procurement_arena import capture_markdown, write_capture

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_cohort_dossiers.py"
spec = importlib.util.spec_from_file_location("check_cohort_dossiers", SCRIPT)
checker = importlib.util.module_from_spec(spec)
sys.modules["check_cohort_dossiers"] = checker
spec.loader.exec_module(checker)

NOW = datetime(2026, 10, 22, tzinfo=UTC)
CONTENT_A = (
    "# Project Alpha\n\nThe board approved the Alpha feasibility study on 1 January 2025.\n\n"
    "Contractor Beta Engineering was named EPCM for the Alpha site.\n"
)
CONTENT_B = "# Tender\n\nThe owner issued a request for temporary power proposals for the Alpha site on 1 July 2025.\n"
QUOTE_A = "The board approved the Alpha feasibility study on 1 January 2025."
QUOTE_B = "The owner issued a request for temporary power proposals for the Alpha site on 1 July 2025."
QUOTE_BUYER = "Contractor Beta Engineering was named EPCM for the Alpha site."


def _write_capture(repo, name, url, content):
    directory = repo / "research" / "cohort-intake" / "us-mining" / "captures"
    directory.mkdir(parents=True, exist_ok=True)
    capture = capture_markdown(url, content, capture_id=name, captured_by="test", captured_at=NOW)
    write_capture(capture, directory / f"{name}.json")
    return f"research/cohort-intake/us-mining/captures/{name}.json", capture.content_sha256


def _signal(signal_id, signal_type, observed_at, capture_path, sha, url, quote, confidence="PROOF_CITED",
            kind="sec_edgar"):
    return {
        "signal_id": signal_id, "signal_type": signal_type, "title": f"title {signal_id}", "observed_at": observed_at,
        "availability_confidence": confidence,
        "availability_evidence": {"kind": kind, "url": "https://example.com/proof", "note": "filing acceptance time"},
        "source_url": url, "capture_path": capture_path, "capture_id": Path(capture_path).stem,
        "source_sha256": sha, "source_quote": quote, "claims": {},
    }


@pytest.fixture
def repo(tmp_path):
    return tmp_path


@pytest.fixture
def dossier(repo):
    path_a, sha_a = _write_capture(repo, "cap-a", "https://example.com/alpha", CONTENT_A)
    path_b, sha_b = _write_capture(repo, "cap-b", "https://example.com/tender", CONTENT_B)
    s1 = _signal("s1", "FEASIBILITY_COMPLETE", "2025-01-01T00:00:00+00:00", path_a, sha_a,
                 "https://example.com/alpha", QUOTE_A)
    s2 = _signal("s2", "EPCM_AWARDED", "2025-03-01T00:00:00+00:00", path_a, sha_a, "https://example.com/alpha",
                 QUOTE_BUYER, confidence="PRINTED_DATE_ONLY", kind="printed_date")
    target = _signal("t1", "PROCUREMENT_SIGNAL", "2025-07-01T00:00:00+00:00", path_b, sha_b,
                     "https://example.com/tender", QUOTE_B)
    target["target_description"] = "Request for temporary power proposals"
    days = (datetime(2025, 7, 1, tzinfo=UTC) - datetime(2025, 1, 1, tzinfo=UTC)).days
    return {
        "schema_version": "trailforge-cohort-dossier-v0", "status": "PROPOSED_UNREVIEWED",
        "project_id": "alpha-mine", "project_name": "Alpha Mine", "vertical": "us-mining", "location": "Nevada, US",
        "owner_or_developer": "Alpha Corp", "selection_note": "synthetic test case",
        "signals": [s1, s2], "target": target,
        "buyer_path": [{"organization": "Beta Engineering", "role": "EPCM", "evidence_signal_id": "s2",
                        "quote": QUOTE_BUYER}],
        "lead_time": {"days": days, "basis": "PROOF_CITED_TIMESTAMPS", "earliest_signal_id": "s1", "note": "test"},
        "target_fit": "TEMPORARY_OR_RENTAL", "target_fit_note": "Solicitation is for temporary power rental.",
        "blockers": [], "reviewer_checklist": ["check proofs"], "created_by": "test-agent",
        "created_at": "2026-10-21T00:00:00+00:00",
    }


def _check(repo, dossier, name=None):
    directory = repo / "research" / "cohort-intake" / dossier.get("vertical", "us-mining") / "dossiers"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{name or dossier['project_id']}.json").write_text(json.dumps(dossier), encoding="utf-8")
    return checker.run(repo / "research" / "cohort-intake", repo_root=repo, now=NOW)


def _errors(repo, dossier):
    (report,) = _check(repo, dossier)
    return report.errors


def _has(errors, text):
    assert any(text in error for error in errors), f"{text!r} not in {errors}"


def test_valid_dossier_passes(repo, dossier):
    (report,) = _check(repo, dossier)
    assert report.errors == []
    assert report.basis == "PROOF_CITED_TIMESTAMPS"
    assert report.signals == 2 and report.has_target


def test_altered_quote_fails(repo, dossier):
    dossier["signals"][0]["source_quote"] = QUOTE_A.replace("approved", "rejected")
    _has(_errors(repo, dossier), "not an exact contiguous substring")


def test_whitespace_normalization_is_not_applied(repo, dossier):
    dossier["signals"][0]["source_quote"] = QUOTE_A.replace(" ", "  ", 1)
    _has(_errors(repo, dossier), "no whitespace or case normalization")


def test_buyer_path_quote_must_be_in_capture(repo, dossier):
    dossier["buyer_path"][0]["quote"] = "Gamma Builders won the EPCM contract for the Alpha site."
    _has(_errors(repo, dossier), "buyer_path[0].quote")


def test_buyer_path_unknown_signal_fails(repo, dossier):
    dossier["buyer_path"][0]["evidence_signal_id"] = "nope"
    _has(_errors(repo, dossier), "is not a signal or target signal_id")


def test_wrong_sha_fails(repo, dossier):
    dossier["signals"][0]["source_sha256"] = "0" * 64
    _has(_errors(repo, dossier), "!= capture content_sha256")


def test_tampered_capture_fails_repo_loader(repo, dossier):
    path = repo / dossier["signals"][0]["capture_path"]
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["content"] += "injected evidence"
    path.write_text(json.dumps(raw), encoding="utf-8")
    _has(_errors(repo, dossier), "failed the repo capture loader")


def test_capture_url_mismatch_fails(repo, dossier):
    dossier["signals"][0]["source_url"] = "https://example.com/other"
    _has(_errors(repo, dossier), "!= capture source_url")


def test_missing_capture_fails(repo, dossier):
    dossier["signals"][0]["capture_path"] = "research/cohort-intake/us-mining/captures/missing.json"
    _has(_errors(repo, dossier), "capture file does not exist")


@pytest.mark.parametrize("bad", ["../outside.json", "research/../../outside.json", "/etc/passwd", "C:/x.json",
                                 "research\\captures\\a.json"])
def test_path_traversal_and_absolute_paths_fail(repo, dossier, bad):
    outside = repo.parent / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    dossier["signals"][0]["capture_path"] = bad
    _has(_errors(repo, dossier), "capture_path must be a repo-relative POSIX path with no '..'")


def test_unc_style_path_fails(repo, dossier):
    dossier["signals"][0]["capture_path"] = "//server/share/cap.json"
    _has(_errors(repo, dossier), "capture_path must be a repo-relative POSIX path")


def test_naive_datetime_fails(repo, dossier):
    dossier["signals"][0]["observed_at"] = "2025-01-01T00:00:00"
    _has(_errors(repo, dossier), "timezone-aware")


def test_future_observed_at_fails(repo, dossier):
    dossier["signals"][1]["observed_at"] = "2027-01-01T00:00:00+00:00"
    _has(_errors(repo, dossier), "is in the future")


def test_verified_by_present_fails(repo, dossier):
    dossier["verified_by"] = "Jane Doe"
    errors = _errors(repo, dossier)
    _has(errors, "verified_by")


def test_nested_verified_by_and_status_strings_fail(repo, dossier):
    dossier["signals"][0]["claims"] = {"verified_by": "x", "note": "verified", "ok": "VERIFIED"}
    errors = _errors(repo, dossier)
    _has(errors, "claims.verified_by")
    _has(errors, "claims.note")
    _has(errors, "claims.ok")


def test_verified_word_inside_prose_is_allowed(repo, dossier):
    dossier["blockers"] = ["Date was verified against nothing yet"]
    assert _errors(repo, dossier) == []


def test_bad_enums_fail(repo, dossier):
    dossier["status"] = "VERIFIED"
    dossier["vertical"] = "space"
    dossier["signals"][0]["signal_type"] = "MADE_UP"
    dossier["signals"][0]["availability_confidence"] = "HIGH"
    dossier["buyer_path"][0]["role"] = "BOSS"
    errors = _errors(repo, dossier)
    for text in ("status:", "vertical:", "signal_type:", "availability_confidence:", "role:"):
        _has(errors, text)


def test_target_must_be_procurement_signal(repo, dossier):
    dossier["target"]["signal_type"] = "PERMIT_FILED"
    _has(_errors(repo, dossier), "target must be PROCUREMENT_SIGNAL")


def test_lead_time_mismatch_fails(repo, dossier):
    dossier["lead_time"]["days"] = 200
    _has(_errors(repo, dossier), "lead_time.days")


def test_lead_time_must_be_verified_when_both_verified(repo, dossier):
    dossier["lead_time"].update(days=None, basis="UNVERIFIED")
    errors = _errors(repo, dossier)
    _has(errors, "expected PROOF_CITED_TIMESTAMPS")
    _has(errors, "lead_time.days")


def test_lead_time_not_provable_with_printed_date(repo, dossier):
    dossier["signals"][0].update(availability_confidence="PRINTED_DATE_ONLY")
    dossier["signals"][0]["availability_evidence"]["kind"] = "printed_date"
    _has(_errors(repo, dossier), "days must be null and basis UNVERIFIED")


def test_earliest_signal_must_be_earliest(repo, dossier):
    dossier["lead_time"]["earliest_signal_id"] = "s2"
    _has(_errors(repo, dossier), "is not the earliest signal")


def test_null_target_requires_unverified_lead_time(repo, dossier):
    dossier["target"] = None
    _has(_errors(repo, dossier), "target is null")
    dossier["lead_time"].update(days=None, basis="UNVERIFIED")
    (report,) = _check(repo, dossier)
    assert report.errors == []
    assert any("unresolved" in warning for warning in report.warnings)


def test_signal_after_target_fails(repo, dossier):
    dossier["signals"][1]["observed_at"] = "2025-08-01T00:00:00+00:00"
    _has(_errors(repo, dossier), "is after target observed_at")


def test_duplicate_signal_ids_fail(repo, dossier):
    dossier["signals"][1]["signal_id"] = "s1"
    dossier["buyer_path"] = []
    _has(_errors(repo, dossier), "duplicate signal_id")


def test_target_id_colliding_with_signal_fails(repo, dossier):
    dossier["target"]["signal_id"] = "s1"
    _has(_errors(repo, dossier), "duplicates a signal")


def test_duplicate_project_id_across_files_fails(repo, dossier):
    _check(repo, dossier)
    reports = _check(repo, dossier, name="alpha-copy")
    errors = [error for report in reports for error in report.errors]
    _has(errors, "duplicate project_id")
    _has(errors, "does not match file name")


def test_evidence_confidence_rules(repo, dossier):
    dossier["signals"][0]["availability_evidence"]["kind"] = "printed_date"
    dossier["signals"][1]["availability_evidence"]["kind"] = "wayback_cdx"
    errors = _errors(repo, dossier)
    _has(errors, "PROOF_CITED cannot rest on kind printed_date")
    _has(errors, "must use kind printed_date or other")


def test_verified_timestamp_requires_url_and_note(repo, dossier):
    dossier["signals"][0]["availability_evidence"].update(url="", note="")
    errors = _errors(repo, dossier)
    _has(errors, "availability_evidence.url")
    _has(errors, "availability_evidence.note")


def test_proposed_requires_two_signals_but_incomplete_does_not(repo, dossier):
    dossier["signals"] = dossier["signals"][:1]
    dossier["buyer_path"] = []
    dossier["lead_time"].update(earliest_signal_id="s1")
    _has(_errors(repo, dossier), "requires at least 2 signals")
    dossier["status"] = "INCOMPLETE"
    dossier["lead_time"].update(days=None, basis="UNVERIFIED")
    assert _errors(repo, dossier) == []


def test_incomplete_may_omit_target(repo, dossier):
    dossier["status"] = "INCOMPLETE"
    dossier["target"] = None
    dossier["lead_time"].update(days=None, basis="UNVERIFIED")
    assert _errors(repo, dossier) == []


def test_unexpected_and_missing_fields_fail(repo, dossier):
    dossier["surprise"] = 1
    del dossier["location"]
    errors = _errors(repo, dossier)
    _has(errors, "unexpected field 'surprise'")
    _has(errors, "missing required field 'location'")


def test_bad_project_id_and_schema_version(repo, dossier):
    dossier["project_id"] = "Bad_ID"
    dossier["schema_version"] = "v9"
    errors = _errors(repo, dossier)
    _has(errors, "project_id")
    _has(errors, "schema_version")


def test_vertical_must_match_directory(repo, dossier):
    directory = repo / "research" / "cohort-intake" / "data-center" / "dossiers"
    directory.mkdir(parents=True)
    (directory / "alpha-mine.json").write_text(json.dumps(dossier), encoding="utf-8")
    (report,) = checker.run(repo / "research" / "cohort-intake", repo_root=repo, now=NOW)
    _has(report.errors, "does not match directory")


def test_all_errors_are_collected(repo, dossier):
    dossier["signals"][0]["source_quote"] = "invented text that is nowhere in the capture at all"
    dossier["signals"][0]["source_sha256"] = "f" * 64
    dossier["signals"][1]["observed_at"] = "2025-03-01T00:00:00"
    dossier["verified_by"] = "someone"
    dossier["lead_time"]["days"] = 1
    dossier["target"]["signal_type"] = "PERMIT_FILED"
    errors = _errors(repo, dossier)
    for text in ("not an exact contiguous", "!= capture content_sha256", "timezone-aware", "verified_by",
                 "target must be PROCUREMENT_SIGNAL"):
        _has(errors, text)
    assert len(errors) >= 5


def test_invalid_json_is_reported(repo):
    directory = repo / "research" / "cohort-intake" / "us-mining" / "dossiers"
    directory.mkdir(parents=True)
    (directory / "broken.json").write_text("{not json", encoding="utf-8")
    (report,) = checker.run(repo / "research" / "cohort-intake", repo_root=repo, now=NOW)
    _has(report.errors, "cannot read dossier JSON")


def test_warnings_short_quote_single_source_and_shared_url(repo, dossier):
    dossier["signals"][0]["source_quote"] = QUOTE_A[:30]
    other = copy.deepcopy(dossier)
    other["project_id"] = "beta-mine"
    other["signals"][1]["source_quote"] = QUOTE_BUYER
    _check(repo, dossier)
    reports = _check(repo, other)
    warnings = [warning for report in reports for warning in report.warnings]
    _has(warnings, "weak evidence")
    _has(warnings, "is also used by")
    only = copy.deepcopy(dossier)
    only["project_id"] = "gamma-mine"
    only["target"] = None
    only["lead_time"].update(days=None, basis="UNVERIFIED")
    only["buyer_path"] = []
    only["status"] = "INCOMPLETE"
    only["signals"][1]["source_quote"] = QUOTE_A
    reports = _check(repo, only)
    gamma = next(report for report in reports if report.project_id == "gamma-mine")
    _has(gamma.warnings, "single-source dossier")


def test_cli_text_and_json_output(repo, dossier, capsys):
    _check(repo, dossier)
    root = repo / "research" / "cohort-intake"
    assert checker.main(["--root", str(root)], repo_root=repo, now=NOW) == 0
    text = capsys.readouterr().out
    assert "PASS" in text and "alpha-mine" in text and "totals:" in text and "lead-time basis" in text

    assert checker.main(["--root", str(root), "--json"], repo_root=repo, now=NOW) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["totals"]["dossiers"] == 1
    assert payload["dossiers"][0]["project_id"] == "alpha-mine"
    assert payload["dossiers"][0]["lead_time_basis"] == "PROOF_CITED_TIMESTAMPS"

    dossier["verified_by"] = "x"
    _check(repo, dossier)
    assert checker.main(["--root", str(root), "--json"], repo_root=repo, now=NOW) == 1
    failed = json.loads(capsys.readouterr().out)
    assert failed["ok"] is False and failed["dossiers"][0]["errors"]


def test_missing_root_exits_nonzero(tmp_path, capsys):
    assert checker.main(["--root", str(tmp_path / "nope")]) == 2


# ---- fix-loop additions -------------------------------------------------------------------------------------------

def test_proof_cited_with_kind_other_fails(repo, dossier):
    dossier["signals"][0]["availability_evidence"]["kind"] = "other"
    _has(_errors(repo, dossier), "PROOF_CITED cannot rest on kind other")


def test_printed_date_only_with_other_is_allowed(repo, dossier):
    dossier["signals"][1]["availability_evidence"]["kind"] = "other"
    assert _errors(repo, dossier) == []


def test_legacy_verified_tokens_are_errors_with_rename_hint(repo, dossier):
    dossier["signals"][0]["availability_confidence"] = "VERIFIED_TIMESTAMP"
    dossier["lead_time"]["basis"] = "VERIFIED_TIMESTAMPS"
    errors = _errors(repo, dossier)
    _has(errors, "VERIFIED_TIMESTAMP was renamed to PROOF_CITED ")
    _has(errors, "VERIFIED_TIMESTAMPS was renamed to PROOF_CITED_TIMESTAMPS")


def test_procurement_signal_forbidden_in_signals(repo, dossier):
    dossier["signals"][1]["signal_type"] = "PROCUREMENT_SIGNAL"
    _has(_errors(repo, dossier), "only allowed as the target, not in signals[]")


def test_later_procurement_events_must_be_strings(repo, dossier):
    dossier["later_procurement_events"] = ["Contract award 2026-01-01"]
    assert _errors(repo, dossier) == []
    dossier["later_procurement_events"] = [1]
    _has(_errors(repo, dossier), "later_procurement_events: must be a list of strings")


def test_duplicate_json_keys_fail(repo, dossier):
    directory = repo / "research" / "cohort-intake" / "us-mining" / "dossiers"
    directory.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dossier).replace('"project_name": "Alpha Mine"', '"project_name": "A", "project_name": "B"')
    (directory / "alpha-mine.json").write_text(text, encoding="utf-8")
    (report,) = checker.run(repo / "research" / "cohort-intake", repo_root=repo, now=NOW)
    _has(report.errors, "duplicate JSON key 'project_name'")


def test_duplicate_json_keys_in_capture_fail(repo, dossier):
    path = repo / dossier["signals"][0]["capture_path"]
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("{", '{\n  "provider": "x", "provider": "y",', 1), encoding="utf-8")
    _has(_errors(repo, dossier), "not strictly valid JSON")


def test_short_quote_is_error_and_medium_quote_is_warning(repo, dossier):
    dossier["signals"][0]["source_quote"] = "Project Alpha"
    _has(_errors(repo, dossier), "quote is only 13 chars; minimum is 20")
    dossier["signals"][0]["source_quote"] = QUOTE_A[:30]
    (report,) = _check(repo, dossier)
    assert report.errors == []
    _has(report.warnings, "weak evidence")


def test_short_buyer_quote_is_error(repo, dossier):
    dossier["buyer_path"][0]["quote"] = "Beta Engineering"
    _has(_errors(repo, dossier), "buyer_path[0].quote: quote is only 16 chars")


def test_buyer_org_not_in_quote_warns(repo, dossier):
    dossier["buyer_path"][0]["organization"] = "Gamma Builders"
    (report,) = _check(repo, dossier)
    assert report.errors == []
    _has(report.warnings, "none of the organization's words")


def test_buyer_quote_from_other_signals_capture_fails(repo, dossier):
    dossier["buyer_path"][0]["evidence_signal_id"] = "s1"
    dossier["buyer_path"][0]["quote"] = QUOTE_B
    _has(_errors(repo, dossier), "buyer_path[0].quote: quote is not an exact contiguous substring")


@pytest.mark.parametrize("value", ["Verified.", "reviewed.", "VERIFIED", "Human reviewed!"])
def test_status_string_with_punctuation_fails(repo, dossier, value):
    dossier["signals"][0]["claims"] = {"flag": value}
    _has(_errors(repo, dossier), "claims verified/reviewed status")


@pytest.mark.parametrize("key", ["reviewed", "approved", "review", "human_review", "signed_off", "verified",
                                 "verified_at", "Reviewed"])
def test_signoff_keys_fail(repo, dossier, key):
    dossier["signals"][0]["claims"] = {key: True}
    _has(_errors(repo, dossier), "reviewer sign-off/verified key is forbidden")


def test_unverified_keys_are_allowed(repo, dossier):
    dossier["signals"][0]["claims"] = {"unverified_note": "agent guess"}
    assert _errors(repo, dossier) == []


def test_symlink_escaping_repo_fails(repo, dossier):
    outside = repo.parent / "outside_capture.json"
    outside.write_text((repo / dossier["signals"][0]["capture_path"]).read_text(encoding="utf-8"), encoding="utf-8")
    link = repo / "research" / "cohort-intake" / "us-mining" / "captures" / "link.json"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    dossier["signals"][0]["capture_path"] = "research/cohort-intake/us-mining/captures/link.json"
    _has(_errors(repo, dossier), "resolves outside the repository")


def test_capture_path_outside_captures_dir_fails(repo, dossier):
    source = repo / dossier["signals"][0]["capture_path"]
    target = repo / "other" / "cap.json"
    target.parent.mkdir()
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    dossier["signals"][0]["capture_path"] = "other/cap.json"
    _has(_errors(repo, dossier), "must be inside research/cohort-intake/us-mining/captures/")


def test_capture_path_in_other_vertical_captures_fails(repo, dossier):
    source = repo / dossier["signals"][0]["capture_path"]
    target = repo / "research" / "cohort-intake" / "data-center" / "captures" / "cap-a.json"
    target.parent.mkdir(parents=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    dossier["signals"][0]["capture_path"] = "research/cohort-intake/data-center/captures/cap-a.json"
    _has(_errors(repo, dossier), "must be inside research/cohort-intake/us-mining/captures/")


def test_z_suffix_is_timezone_aware(repo, dossier):
    dossier["signals"][0]["observed_at"] = "2025-01-01T00:00:00Z"
    assert _errors(repo, dossier) == []


@pytest.mark.parametrize("bad, text", [("2025-01-01", "timezone-aware"), ("2025-02-30T00:00:00+00:00", "not a valid"),
                                       ("1985-01-01T00:00:00+00:00", "before 1990")])
def test_bad_observed_at_forms_fail(repo, dossier, bad, text):
    dossier["signals"][0]["observed_at"] = bad
    _has(_errors(repo, dossier), text)


def test_observed_after_captured_at_fails(repo, dossier):
    path = repo / dossier["signals"][0]["capture_path"]
    capture = capture_markdown("https://example.com/alpha", CONTENT_A, capture_id="cap-a", captured_by="test",
                               captured_at=datetime(2024, 6, 1, tzinfo=UTC))
    path.unlink()
    write_capture(capture, path)
    _has(_errors(repo, dossier), "is after the capture's captured_at")


@pytest.mark.parametrize("days", [float("nan"), True, "181", float("inf")])
def test_bad_days_values_fail(repo, dossier, days):
    dossier["lead_time"]["days"] = days
    _has(_errors(repo, dossier), "lead_time.days")


def test_mixed_offset_lead_time(repo, dossier):
    dossier["signals"][0]["observed_at"] = "2025-01-01T00:00:00+11:00"
    dossier["signals"][1]["observed_at"] = "2025-03-01T00:00:00+00:00"
    dossier["target"]["observed_at"] = "2025-07-01T00:00:00-05:00"
    expected = (datetime.fromisoformat("2025-07-01T00:00:00-05:00")
                - datetime.fromisoformat("2025-01-01T00:00:00+11:00")).total_seconds() / 86400
    dossier["lead_time"]["days"] = 181
    _has(_errors(repo, dossier), "lead_time.days")
    dossier["lead_time"]["days"] = expected
    assert _errors(repo, dossier) == []


def test_incomplete_with_proof_cited_lead_time_fails(repo, dossier):
    dossier["status"] = "INCOMPLETE"
    _has(_errors(repo, dossier), "INCOMPLETE dossiers must have days null and basis UNVERIFIED")


def test_recursion_error_is_reported_per_file(repo, dossier):
    _check(repo, dossier)
    directory = repo / "research" / "cohort-intake" / "us-mining" / "dossiers"
    (directory / "deep-nest.json").write_text("[" * 200000 + "]" * 200000, encoding="utf-8")
    reports = checker.run(repo / "research" / "cohort-intake", repo_root=repo, now=NOW)
    by_name = {Path(report.path).stem: report for report in reports}
    _has(by_name["deep-nest"].errors, "nested too deeply")
    assert by_name["alpha-mine"].errors == []


def test_explicit_empty_root_exits_2_default_empty_exits_0(repo, capsys):
    (repo / "research" / "cohort-intake").mkdir(parents=True)
    root = repo / "research" / "cohort-intake"
    assert checker.main(["--root", str(root)], repo_root=repo, now=NOW) == 2
    assert checker.main([], repo_root=repo, now=NOW) == 0


def test_target_fit_required_with_target(repo, dossier):
    del dossier["target_fit"]
    del dossier["target_fit_note"]
    errors = _errors(repo, dossier)
    _has(errors, "dossier.target_fit:")
    _has(errors, "target_fit_note")


def test_target_fit_bad_enum_and_short_note(repo, dossier):
    dossier["target_fit"] = "RENTAL"
    dossier["target_fit_note"] = "too short"
    errors = _errors(repo, dossier)
    _has(errors, "target_fit: 'RENTAL' is not one of")
    _has(errors, "target_fit_note: must be a string of at least 20")


@pytest.mark.parametrize("fit", ["PERMIT_OR_STATUS_ONLY", "PERMANENT_PLANT_OR_GRID"])
def test_weak_target_fit_warns_but_passes(repo, dossier, fit):
    dossier["target_fit"] = fit
    (report,) = _check(repo, dossier)
    assert report.errors == []
    _has(report.warnings, "reviewer: consider target null")


def test_null_target_needs_no_target_fit(repo, dossier):
    dossier["target"] = None
    del dossier["target_fit"]
    del dossier["target_fit_note"]
    dossier["lead_time"].update(days=None, basis="UNVERIFIED")
    assert _errors(repo, dossier) == []


def test_wayback_warning_unless_snapshot_url(repo, dossier):
    dossier["signals"][0]["availability_evidence"]["kind"] = "wayback_cdx"
    (report,) = _check(repo, dossier)
    _has(report.warnings, "Wayback proves the URL existed, not that this text did")


def test_unsupported_numeric_claim_warns(repo, dossier):
    dossier["signals"][0]["claims"] = {"year": 2025, "mw": 17.5, "nested": {"count": 3}}
    (report,) = _check(repo, dossier)
    assert report.errors == []
    warnings = [w for w in report.warnings if "claim not literally supported" in w]
    assert len(warnings) == 2 and any("mw" in w for w in warnings) and any("count" in w for w in warnings)
