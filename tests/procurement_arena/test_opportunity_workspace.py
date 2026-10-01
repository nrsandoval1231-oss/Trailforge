import hashlib
import json
from datetime import UTC, datetime

import pytest

from athena_procurement_arena.opportunity_workspace import import_opportunity, render_workspace
from athena_procurement_arena.public_capture import capture_markdown, write_capture

NOW = datetime(2026, 10, 1, 12, tzinfo=UTC)
CONTENT = ("PSEG Long Island published 2026-07-27. This 2026 Temporary Generation RFP closes "
           "2026-10-30T17:00:00-04:00. Temporary generation solicitation requires 5 MW per project; "
           "the total program is up to 400 MW. An older deadline was 2026-09-30T17:00:00-04:00. "
           "A dispatchable power purchase agreement is requested.")


def make_capture(tmp_path):
    path = tmp_path / "source.capture.json"
    capture = capture_markdown("https://example.com/rfp", CONTENT, capture_id="source-1", captured_by="reviewer",
                               captured_at=NOW, provider="firecrawl", provider_job_id="job-1")
    write_capture(capture, path)
    sidecar = {"retrieved_at": NOW.isoformat(),
               "freshness_requested_max_age_ms": 0, "cache_state": "UNKNOWN", "capture_sha256": capture.content_sha256}
    path.with_name("source.acquisition.json").write_text(json.dumps(sidecar))
    return path


def input_record(tmp_path, capture, *, kind="ACTIVE_RFP", deadline="2026-10-30T17:00:00-04:00",
                 opportunity_id="lipa-rfp", identity=None, include_quotes=True):
    identity = identity or {"organization": "PSEG Long Island", "official_id": "2026 Temporary Generation RFP"}
    path_ref = capture.name
    evidence = {
        "title": {"capture_file": path_ref, "quote": "2026 Temporary Generation RFP"},
        **{f"identity.{key}": {"capture_file": path_ref, "quote": value} for key, value in identity.items() if value},
    }
    requirements = {"required_kw": 5000, "program_mw": 400,
                    "scope": "Temporary generation under a power purchase agreement",
                    "fuel": None}
    requirement_quotes = {"required_kw": {"capture_file": path_ref, "quote": "5 MW per project"},
                          "program_mw": {"capture_file": path_ref, "quote": "up to 400 MW"},
                          "scope": {"capture_file": path_ref, "quote": "A dispatchable power purchase agreement is requested."}}
    requirements["scope"] = "Temporary generation under a power purchase agreement"
    if not include_quotes:
        requirement_quotes.pop("required_kw")
    record = {"schema_version": "trailforge-opportunity-input-v1", "opportunity_id": opportunity_id,
        "kind": kind, "title": "2026 Temporary Generation RFP", "identity": identity,
        "reviewed_by": "reviewer-1", "reviewed_at": NOW.isoformat(),
        "sources": [{"capture_file": path_ref, "source_type": "official-solicitation", "title": "RFP page",
                     "freshness_requested_max_age_ms": 0, "cache_state": "UNKNOWN", "completed_at": NOW.isoformat()}],
        "field_evidence": evidence, "published_at": {"value": "2026-07-27", "capture_file": path_ref,
            "quote": "2026-07-27"},
        "deadline": {"value": deadline, "capture_file": path_ref, "quote": deadline},
        "requirements": requirements, "requirement_quotes": requirement_quotes,
        "signal_family": "temporary-power-procurement", "power_gap_hypothesis": "Potential short-term power gap",
        "direct_buyer_orgs": [], "roles": [], "earliest_signal": {"value": "2026-07-27", "capture_file": path_ref,
            "quote": "2026-07-27"}, "next_action": "Review source documents",
        "documents": [{"title": "RFP PDF", "url": "https://example.com/rfp.pdf", "source_type": "PDF"}],
        "notes": ""}
    out = tmp_path / f"{opportunity_id}.json"
    out.write_text(json.dumps(record), encoding="utf-8")
    return out


def test_active_rfp_preserves_multiple_requirements_but_does_not_treat_aggregate_as_load(tmp_path):
    capture = make_capture(tmp_path)
    input_path = input_record(tmp_path, capture)
    record = import_opportunity(input_path, tmp_path / "workspace", now=NOW)
    assert record["deadline"]["value"] == "2026-10-30T17:00:00-04:00"
    assert record["published_at"]["value"] == "2026-07-27"
    assert len(record["sources"]) == 1
    assert record["qualification"]["status"] == "NOT_FIT"
    assert record["qualification"]["lifecycle_status"] == "OPEN_AS_OF_PUBLIC_SOURCE"
    assert record["qualification"]["amendments_status"] == "UNKNOWN"
    assert "PERMANENT_CAPACITY_OR_PPA_SCOPE" in record["qualification"]["reason_codes"]
    assert record["requirements"]["required_kw"] == 5000
    assert record["requirements"]["program_mw"] == 400
    html = render_workspace(tmp_path / "workspace", tmp_path / "workspace" / "index.html").read_text()
    assert "ACTIVE RFPs" in html and "UNKNOWN" in html and "400" in html
    assert "NOT_FIT" in html and "OPEN_AS_OF_PUBLIC_SOURCE" in html
    assert "Local capture" in html and "#lipa-rfp" in html
    assert all(line == line.rstrip() for line in html.splitlines())


def test_active_rfp_expired_deadline_fails_closed_and_dates_may_have_day_precision(tmp_path):
    capture = make_capture(tmp_path)
    record = import_opportunity(input_record(tmp_path, capture, deadline="2026-09-30T17:00:00-04:00"),
                                tmp_path / "workspace", now=NOW)
    assert record["qualification"]["lifecycle_status"] == "EXPIRED"
    assert record["qualification"]["status"] == "NOT_CURRENT"
    assert record["earliest_signal"]["value"] == "2026-07-27"


def test_known_requirement_requires_literal_citation_and_bad_citation_is_rejected(tmp_path):
    capture = make_capture(tmp_path)
    with pytest.raises(ValueError, match="exact source quote"):
        import_opportunity(input_record(tmp_path, capture, include_quotes=False), tmp_path / "workspace", now=NOW)
    raw = json.loads(input_record(tmp_path, capture).read_text())
    raw["requirement_quotes"]["required_kw"]["quote"] = "500 MW total program"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="exact span"):
        import_opportunity(bad, tmp_path / "other", now=NOW)


def test_identity_ambiguity_does_not_merge_and_same_identity_merges_source_history(tmp_path):
    capture = make_capture(tmp_path)
    workspace = tmp_path / "workspace"
    a = import_opportunity(input_record(tmp_path, capture, kind="PRE_RFP_PROJECT", identity={"organization": "PSEG Long Island"},
                                        opportunity_id="early-a"), workspace, now=NOW)
    assert a["identity_resolution"] == "UNKNOWN"
    duplicate_path = input_record(tmp_path, capture, kind="PRE_RFP_PROJECT", identity={"organization": "PSEG Long Island"},
                                  opportunity_id="early-b")
    b = import_opportunity(duplicate_path, workspace, now=NOW)
    assert b["opportunity_id"] == "early-b"
    manifest = json.loads((workspace / "workspace.json").read_text())
    assert len(manifest["opportunities"]) == 2


def test_same_content_new_capture_version_is_retained_by_capture_hash(tmp_path):
    first = make_capture(tmp_path)
    second = tmp_path / "source-v2.capture.json"
    from athena_procurement_arena.public_capture import load_capture, write_capture
    capture = load_capture(first)
    replacement = capture_markdown(capture.source_url, capture.content, capture_id="source-2", captured_by="reviewer",
                                   captured_at=datetime(2026, 10, 1, 13, tzinfo=UTC), provider="firecrawl", provider_job_id="job-2")
    write_capture(replacement, second)
    second.with_name("source-v2.acquisition.json").write_text(json.dumps({"retrieved_at": NOW.isoformat(),
        "freshness_requested_max_age_ms": 0, "cache_state": "UNKNOWN", "capture_sha256": replacement.content_sha256}))
    record_file = input_record(tmp_path, first)
    raw = json.loads(record_file.read_text())
    raw["sources"].append({"capture_file": second.name})
    record_file.write_text(json.dumps(raw))
    record = import_opportunity(record_file, tmp_path / "workspace", now=NOW)
    assert len(record["sources"]) == 2
    assert len({item["capture_hash"] for item in record["sources"].values()}) == 2


def test_dedup_preserves_and_flags_conflicting_requirements(tmp_path):
    first = make_capture(tmp_path)
    workspace = tmp_path / "workspace"
    import_opportunity(input_record(tmp_path, first), workspace, now=NOW)
    text = CONTENT + " Another schedule states 6 MW per project."
    second_capture = tmp_path / "source-v2.capture.json"
    version = capture_markdown("https://example.com/rfp", text, capture_id="source-v2", captured_by="reviewer",
                               captured_at=NOW, provider="firecrawl", provider_job_id="job-v2")
    write_capture(version, second_capture)
    second_capture.with_name("source-v2.acquisition.json").write_text(json.dumps({"retrieved_at": NOW.isoformat(),
        "freshness_requested_max_age_ms": 0, "cache_state": "UNKNOWN", "capture_sha256": version.content_sha256}))
    second = input_record(tmp_path, first, opportunity_id="lipa-rfp-copy")
    raw = json.loads(second.read_text())
    for item in raw["sources"]:
        item["capture_file"] = second_capture.name
    for evidence in raw["field_evidence"].values():
        evidence["capture_file"] = second_capture.name
    for evidence in raw["requirement_quotes"].values():
        evidence["capture_file"] = second_capture.name
    raw["requirement_quotes"]["required_kw"]["quote"] = "6 MW per project"
    raw["requirement_quotes"]["required_kw"]["value"] = 6000
    raw["requirements"]["required_kw"] = 6000
    second.write_text(json.dumps(raw))
    merged = import_opportunity(second, workspace, now=NOW)
    assert merged["requirements"]["required_kw"] is None
    assert "required_kw" in merged["requirement_conflicts"]
    assert len(merged["evidence_history"]) == 2
    assert merged["evidence_history"][0]["title"] == "2026 Temporary Generation RFP"
    assert merged["evidence_history"][1]["opportunity_id"] == "lipa-rfp-copy"


def test_same_identity_changed_schedule_keeps_both_dates_and_blocks_active_status(tmp_path):
    first = make_capture(tmp_path)
    workspace = tmp_path / "workspace"
    import_opportunity(input_record(tmp_path, first), workspace, now=NOW)

    text = CONTENT + " Amended schedule: submissions now close 2026-11-15T17:00:00-05:00."
    second_capture = tmp_path / "schedule-v2.capture.json"
    version = capture_markdown("https://example.com/rfp", text, capture_id="schedule-v2", captured_by="reviewer",
                               captured_at=NOW, provider="firecrawl", provider_job_id="schedule-v2")
    write_capture(version, second_capture)
    second_capture.with_name("schedule-v2.acquisition.json").write_text(json.dumps({
        "retrieved_at": NOW.isoformat(), "freshness_requested_max_age_ms": 0,
        "cache_state": "UNKNOWN", "capture_sha256": version.content_sha256}))
    second = input_record(tmp_path, first, opportunity_id="lipa-rfp-amended")
    raw = json.loads(second.read_text())
    for item in raw["sources"]:
        item["capture_file"] = second_capture.name
    for evidence in raw["field_evidence"].values():
        evidence["capture_file"] = second_capture.name
    for evidence in raw["requirement_quotes"].values():
        evidence["capture_file"] = second_capture.name
    raw["deadline"] = {"value": "2026-11-15T17:00:00-05:00", "capture_file": second_capture.name,
                       "quote": "Amended schedule: submissions now close 2026-11-15T17:00:00-05:00."}
    second.write_text(json.dumps(raw))

    merged = import_opportunity(second, workspace, now=NOW)
    assert merged["deadline"] is None
    assert [item["value"] for item in merged["date_conflicts"]["deadline"]] == [
        "2026-10-30T17:00:00-04:00", "2026-11-15T17:00:00-05:00"]
    assert all(item["capture_hash"] for item in merged["date_conflicts"]["deadline"])
    assert merged["qualification"]["status"] == "NEEDS_REVIEW"
    assert merged["qualification"]["lifecycle_status"] == "UNKNOWN"
    assert "CONFLICTING_SOURCE_DATES_REQUIRE_HUMAN_REVIEW" in merged["qualification"]["reason_codes"]
    html = render_workspace(workspace, workspace / "index.html").read_text()
    assert "Date conflict: deadline" in html and "human review required." in html
    assert "2026-11-15T17:00:00-05:00" in html

    # A subsequent schedule that advances the close date into the past is also a conflict,
    # never an opportunity to reuse the old fresh deadline or silently pick the newest claim.
    third = input_record(tmp_path, first, opportunity_id="lipa-rfp-closed")
    closed = json.loads(third.read_text())
    for item in closed["sources"]:
        item["capture_file"] = second_capture.name
    for evidence in closed["field_evidence"].values():
        evidence["capture_file"] = second_capture.name
    for evidence in closed["requirement_quotes"].values():
        evidence["capture_file"] = second_capture.name
    closed["deadline"] = {"value": "2026-09-30T17:00:00-04:00", "capture_file": second_capture.name,
                          "quote": "2026-09-30T17:00:00-04:00"}
    third.write_text(json.dumps(closed))
    merged_closed = import_opportunity(third, workspace, now=NOW)
    deadlines = merged_closed["date_conflicts"]["deadline"]
    assert [item["value"] for item in deadlines] == [
        "2026-10-30T17:00:00-04:00", "2026-11-15T17:00:00-05:00", "2026-09-30T17:00:00-04:00"]
    assert merged_closed["deadline"] is None
    assert merged_closed["qualification"]["status"] == "NEEDS_REVIEW"
    assert merged_closed["qualification"]["lifecycle_status"] == "UNKNOWN"


def test_conflicting_published_and_earliest_signal_dates_are_unknown_with_citations(tmp_path):
    first = make_capture(tmp_path)
    workspace = tmp_path / "workspace"
    import_opportunity(input_record(tmp_path, first), workspace, now=NOW)
    second_capture = tmp_path / "signal-v2.capture.json"
    text = CONTENT + " Updated notice date: 2026-07-28. First project signal appeared 2026-07-29."
    version = capture_markdown("https://example.com/rfp", text, capture_id="signal-v2", captured_by="reviewer",
                               captured_at=NOW, provider="firecrawl", provider_job_id="signal-v2")
    write_capture(version, second_capture)
    second_capture.with_name("signal-v2.acquisition.json").write_text(json.dumps({
        "retrieved_at": NOW.isoformat(), "freshness_requested_max_age_ms": 0,
        "cache_state": "UNKNOWN", "capture_sha256": version.content_sha256}))
    second = input_record(tmp_path, first, opportunity_id="lipa-rfp-date-revision")
    raw = json.loads(second.read_text())
    for item in raw["sources"]:
        item["capture_file"] = second_capture.name
    for evidence in raw["field_evidence"].values():
        evidence["capture_file"] = second_capture.name
    for evidence in raw["requirement_quotes"].values():
        evidence["capture_file"] = second_capture.name
    raw["published_at"] = {"value": "2026-07-28", "capture_file": second_capture.name,
                            "quote": "Updated notice date: 2026-07-28."}
    raw["earliest_signal"] = {"value": "2026-07-29", "capture_file": second_capture.name,
                              "quote": "First project signal appeared 2026-07-29."}
    second.write_text(json.dumps(raw))
    merged = import_opportunity(second, workspace, now=NOW)
    assert merged["published_at"] is None and merged["earliest_signal"] is None
    for field, new_value in (("published_at", "2026-07-28"), ("earliest_signal", "2026-07-29")):
        candidates = merged["date_conflicts"][field]
        assert [item["value"] for item in candidates] == ["2026-07-27", new_value]
        assert all(item["capture_hash"] and item["capture_sha256"] and item["quote"] for item in candidates)
    assert merged["qualification"]["status"] == "NEEDS_REVIEW"
    assert merged["qualification"]["lifecycle_status"] == "UNKNOWN"


def test_deadline_freshness_must_match_the_cited_deadline_capture(tmp_path):
    deadline_capture = make_capture(tmp_path)
    old = json.loads(deadline_capture.with_name("source.acquisition.json").read_text())
    old["retrieved_at"] = "2026-09-01T12:00:00+00:00"
    deadline_capture.with_name("source.acquisition.json").write_text(json.dumps(old))
    unrelated = tmp_path / "unrelated.capture.json"
    capture = capture_markdown("https://example.com/other", CONTENT, capture_id="unrelated", captured_by="reviewer",
        captured_at=NOW, provider="firecrawl", provider_job_id="other-job")
    write_capture(capture, unrelated)
    unrelated.with_name("unrelated.acquisition.json").write_text(json.dumps({"retrieved_at": NOW.isoformat(),
        "freshness_requested_max_age_ms": 0, "cache_state": "UNKNOWN", "capture_sha256": capture.content_sha256}))
    record_file = input_record(tmp_path, deadline_capture)
    raw = json.loads(record_file.read_text())
    raw["sources"].append({"capture_file": unrelated.name})
    record_file.write_text(json.dumps(raw))
    record = import_opportunity(record_file, tmp_path / "workspace", now=NOW)
    assert record["qualification"]["status"] == "NEEDS_REVIEW"
    assert record["qualification"]["lifecycle_status"] == "UNKNOWN"


@pytest.mark.parametrize("artifact", ["capture", "original"])
def test_render_verifies_retained_capture_and_original_hashes(tmp_path, artifact):
    capture = make_capture(tmp_path)
    original = tmp_path / "notice.pdf"
    original.write_bytes(b"original PDF bytes")
    input_path = input_record(tmp_path, capture)
    raw = json.loads(input_path.read_text())
    raw["documents"][0]["original_file"] = original.name
    raw["documents"][0]["sha256"] = hashlib.sha256(original.read_bytes()).hexdigest()
    input_path.write_text(json.dumps(raw))
    workspace = tmp_path / "workspace"
    imported = import_opportunity(input_path, workspace, now=NOW)
    if artifact == "capture":
        stored = workspace / next(iter(imported["sources"].values()))["capture_file"]
    else:
        stored = workspace / imported["documents"][0]["original_file"]
    stored.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash|cannot be verified"):
        render_workspace(workspace, workspace / "index.html")


def test_import_refuses_to_launder_a_tampered_existing_record(tmp_path):
    capture = make_capture(tmp_path)
    workspace = tmp_path / "workspace"
    import_opportunity(input_record(tmp_path, capture), workspace, now=NOW)
    manifest_path = workspace / "workspace.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["opportunities"][0]["notes"] = "changed without evidence"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="existing opportunity record hash mismatch"):
        import_opportunity(input_record(tmp_path, capture, opportunity_id="second"), workspace, now=NOW)


def test_html_escapes_untrusted_text_and_record_tampering_is_visible(tmp_path):
    record_path = input_record(tmp_path, make_capture(tmp_path))
    raw = json.loads(record_path.read_text())
    attack = "Temporary <img src=x onerror=alert(1)> generation under a power purchase agreement"
    content = CONTENT + " " + attack
    malicious_capture = tmp_path / "malicious.capture.json"
    write_capture(capture_markdown("https://example.com/x?ok=1&x=2", content, capture_id="malicious",
        captured_by="reviewer", captured_at=NOW), malicious_capture)
    raw["sources"][0]["capture_file"] = malicious_capture.name
    for citation in raw["field_evidence"].values():
        citation["capture_file"] = malicious_capture.name
    for citation in raw["requirement_quotes"].values():
        citation["capture_file"] = malicious_capture.name
    raw["requirements"]["scope"] = attack
    raw["requirement_quotes"]["scope"]["quote"] = attack
    record_path.write_text(json.dumps(raw))
    workspace = tmp_path / "workspace"
    import_opportunity(record_path, workspace, now=NOW)
    target = render_workspace(workspace, workspace / "index.html")
    assert "<img src=x" not in target.read_text()
    assert "&lt;img src=x" in target.read_text()
    manifest = json.loads((workspace / "workspace.json").read_text())
    manifest["opportunities"][0]["notes"] = "tampered"
    (workspace / "workspace.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="record hash mismatch"):
        render_workspace(workspace, workspace / "index.html")
