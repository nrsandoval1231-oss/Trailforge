import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from athena_procurement_arena.opportunity_workspace import import_opportunity, render_workspace
from athena_procurement_arena.public_capture import capture_markdown, write_capture

NOW = datetime.now(UTC)
# Clearly synthetic fixture text; no real project, buyer or contact is represented.
CONTENT = ("FIXTURE site plan: Hillcrest Campus, Prairie County, TX. Owner: Fixture Compute Holdings. "
           "Construction requires 12 MW temporary construction power until utility energization. "
           "Procurement route: Fixture Compute Holdings Purchasing portal.")


def write_sidecar(path, capture):
    sidecar = {"schema_version": "trailforge-firecrawl-acquisition-v1", "capture_id": capture.capture_id,
               "source_url": capture.source_url, "retrieved_at": NOW.isoformat(), "completed_at": NOW.isoformat(),
               "freshness_requested_max_age_ms": 0, "cache_state": "MISS", "capture_sha256": capture.content_sha256}
    path.with_name(path.name.replace(".capture.json", ".acquisition.json")).write_text(json.dumps(sidecar))


def capture_file(tmp_path, *, name="source"):
    path = tmp_path / f"{name}.capture.json"
    capture = capture_markdown("https://example.com/site-plan", CONTENT, capture_id=name, captured_by="reviewer",
                               captured_at=NOW, provider="firecrawl", provider_job_id="job-1")
    write_capture(capture, path)
    write_sidecar(path, capture)
    return path.name


def pre_rfp(tmp_path, *, source_type="planning-record", buyer=True, buyer_type=None, name="hillcrest"):
    ref = capture_file(tmp_path, name=name)
    cite = lambda quote: {"capture_file": ref, "quote": quote}  # noqa: E731
    item = {"schema_version": "trailforge-opportunity-input-v1", "opportunity_id": name, "kind": "PRE_RFP_PROJECT",
            "title": "Hillcrest Campus", "reviewed_by": "reviewer", "reviewed_at": NOW.isoformat(),
            "identity": {"organization": "Fixture Compute Holdings", "project": "Hillcrest Campus",
                         "location": "Prairie County, TX"},
            "sources": [{"capture_file": ref, "source_type": source_type}],
            "field_evidence": {"title": cite("Hillcrest Campus"),
                               "identity.organization": cite("Fixture Compute Holdings"),
                               "identity.project": cite("Hillcrest Campus"),
                               "identity.location": cite("Prairie County, TX")},
            "requirements": {"required_kw": 12000, "scope": "temporary construction power"},
            "requirement_quotes": {"required_kw": cite("12 MW temporary construction power"),
                                   "scope": cite("temporary construction power")},
            "power_gap_hypothesis": "Utility energization may trail construction need"}
    if buyer:
        item["direct_buyer_orgs"] = ["Fixture Compute Holdings"]
        item["procurement_route"] = "Fixture Compute Holdings Purchasing portal"
        item["field_evidence"]["direct_buyer_orgs"] = cite("Fixture Compute Holdings")
        item["field_evidence"]["procurement_route"] = cite("Fixture Compute Holdings Purchasing portal")
    if buyer_type:
        item["buyer_type"] = buyer_type
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(item), encoding="utf-8")
    return path


def test_news_only_signal_is_a_research_target_not_a_qualified_opportunity(tmp_path):
    record = import_opportunity(pre_rfp(tmp_path, source_type="news"), tmp_path / "ws", now=NOW)
    html_path = render_workspace(tmp_path / "ws", tmp_path / "ws" / "index.html")
    page = html_path.read_text(encoding="utf-8")
    assert record["kind"] == "PRE_RFP_PROJECT"
    assert "RESEARCH_TARGET_ONLY" in page and "NO_PRIMARY_SOURCE_FOR_POWER_REQUIREMENT" in page
    assert "Find a primary source" in page


def test_primary_source_signal_separates_facts_inference_and_unknowns(tmp_path):
    import_opportunity(pre_rfp(tmp_path), tmp_path / "ws", now=NOW)
    page = render_workspace(tmp_path / "ws", tmp_path / "ws" / "index.html").read_text(encoding="utf-8")
    assert "ACTIONABLE_SIGNAL" in page and "PRE_RFP_SIGNAL" in page
    assert "12 MW temporary construction power" in page          # cited fact
    assert "OPERATOR_HYPOTHESIS_UNCITED" in page                 # inference is labeled, never a fact
    assert "<span class='tag'>UNKNOWN</span> deadline" in page   # unpublished deadline stays unknown
    assert "nothing is sent" in page


def test_primary_source_without_buyer_route_is_candidate_with_identification_action(tmp_path):
    import_opportunity(pre_rfp(tmp_path, buyer=False), tmp_path / "ws", now=NOW)
    page = render_workspace(tmp_path / "ws", tmp_path / "ws" / "index.html").read_text(encoding="utf-8")
    assert "SIGNAL_CANDIDATE" in page and "BUYER_ROUTE_NOT_EVIDENCED" in page
    assert "Identify the owner, EPC or utility procurement route" in page


@pytest.mark.parametrize("buyer_type", ["competitor", "RERENTER"])
def test_competitor_and_rerenter_buyers_are_excluded(tmp_path, buyer_type):
    import_opportunity(pre_rfp(tmp_path, buyer_type=buyer_type), tmp_path / "ws", now=NOW)
    page = render_workspace(tmp_path / "ws", tmp_path / "ws" / "index.html").read_text(encoding="utf-8")
    assert "EXCLUDED_BUYER" in page and "Do not pursue" in page


def test_invalid_buyer_type_and_uncited_procurement_route_are_rejected(tmp_path):
    path = pre_rfp(tmp_path, buyer_type="friend")
    with pytest.raises(ValueError, match="buyer_type"):
        import_opportunity(path, tmp_path / "ws", now=NOW)
    item = json.loads(pre_rfp(tmp_path, name="other").read_text())
    del item["field_evidence"]["procurement_route"]
    path.write_text(json.dumps(item), encoding="utf-8")
    with pytest.raises(ValueError, match="procurement_route"):
        import_opportunity(path, tmp_path / "ws2", now=NOW)


def test_repeated_ingestion_keeps_one_record_and_fresh_process_reload_shows_brief(tmp_path):
    first = pre_rfp(tmp_path)
    import_opportunity(first, tmp_path / "ws", now=NOW)
    again = json.loads(first.read_text())
    again["opportunity_id"] = "hillcrest-rerun"
    second = tmp_path / "again.json"
    second.write_text(json.dumps(again), encoding="utf-8")
    import_opportunity(second, tmp_path / "ws", now=NOW)
    manifest = json.loads((tmp_path / "ws" / "workspace.json").read_text())
    assert len(manifest["opportunities"]) == 1
    code = ("import sys;from athena_procurement_arena.opportunity_workspace import render_workspace as r;"
            "print(r(sys.argv[1], sys.argv[2]))")
    src = str(Path(__file__).resolve().parents[2] / "src")
    out = subprocess.run([sys.executable, "-c", code, str(tmp_path / "ws"), str(tmp_path / "ws" / "fresh.html")],
                         capture_output=True, text=True, env={"PYTHONPATH": src}, check=True)
    assert "ACTIONABLE_SIGNAL" in Path(out.stdout.strip()).read_text(encoding="utf-8")


def test_active_rfp_stays_distinct_and_expired_solicitation_is_historical(tmp_path):
    ref = capture_file(tmp_path, name="rfp")
    cite = lambda quote: {"capture_file": ref, "quote": quote}  # noqa: E731
    item = {"schema_version": "trailforge-opportunity-input-v1", "opportunity_id": "old-rfp", "kind": "ACTIVE_RFP",
            "title": "Hillcrest Campus", "reviewed_by": "reviewer", "reviewed_at": NOW.isoformat(),
            "identity": {"organization": "Fixture Compute Holdings", "official_id": "Hillcrest Campus"},
            "sources": [{"capture_file": ref, "source_type": "official-solicitation"}],
            "field_evidence": {"title": cite("Hillcrest Campus"),
                               "identity.organization": cite("Fixture Compute Holdings"),
                               "identity.official_id": cite("Hillcrest Campus")},
            "published_at": {"value": "2026-01-01", **cite("Hillcrest Campus")},
            "deadline": {"value": "2026-02-01T17:00:00-05:00", **cite("Hillcrest Campus")}}
    path = tmp_path / "rfp.json"
    path.write_text(json.dumps(item), encoding="utf-8")
    import_opportunity(path, tmp_path / "ws", now=NOW)
    page = render_workspace(tmp_path / "ws", tmp_path / "ws" / "index.html").read_text(encoding="utf-8")
    assert "ACTIVE_RFP" in page and "NOT_CURRENT" in page and "historical research only" in page


def test_cited_diesel_only_fuel_makes_a_pre_rfp_signal_not_fit(tmp_path):
    path = pre_rfp(tmp_path)
    item = json.loads(path.read_text())
    ref = item["sources"][0]["capture_file"]
    item["requirements"]["fuel"] = "diesel"
    item["requirement_quotes"]["fuel"] = {"capture_file": ref, "quote": "temporary construction power"}
    path.write_text(json.dumps(item), encoding="utf-8")
    import_opportunity(path, tmp_path / "ws", now=NOW)
    page = render_workspace(tmp_path / "ws", tmp_path / "ws" / "index.html").read_text(encoding="utf-8")
    assert "INCOMPATIBLE_FUEL_CITED" in page and "historical research only" in page


def _page(tmp_path):
    return render_workspace(tmp_path / "ws", tmp_path / "ws" / "index.html").read_text(encoding="utf-8")


def _edit(tmp_path, mutate, **kwargs):
    path = pre_rfp(tmp_path, **kwargs)
    item = json.loads(path.read_text())
    mutate(item, item["sources"][0]["capture_file"])
    path.write_text(json.dumps(item), encoding="utf-8")
    return path


def test_non_power_requirement_does_not_establish_power_relevance(tmp_path):
    def only_scope(item, ref):
        item["requirements"] = {"scope": "temporary construction power"}
        item["requirement_quotes"] = {"scope": item["requirement_quotes"]["scope"]}
    import_opportunity(_edit(tmp_path, only_scope), tmp_path / "ws", now=NOW)
    page = _page(tmp_path)
    assert "POWER_RELEVANCE_NOT_CITED" in page and "ACTIONABLE_SIGNAL" not in page


def test_power_requirement_backed_only_by_news_stays_research_target(tmp_path):
    def mixed_sources(item, ref):
        item["sources"][0]["source_type"] = "news"
    import_opportunity(_edit(tmp_path, mixed_sources), tmp_path / "ws", now=NOW)
    assert "NO_PRIMARY_SOURCE_FOR_POWER_REQUIREMENT" in _page(tmp_path)


def test_dual_fuel_with_gas_is_not_rejected_as_diesel(tmp_path):
    def dual(item, ref):
        item["requirements"]["fuel"] = "natural gas primary, diesel backup"
        item["requirement_quotes"]["fuel"] = {"capture_file": ref, "quote": "temporary construction power"}
    import_opportunity(_edit(tmp_path, dual), tmp_path / "ws", now=NOW)
    page = _page(tmp_path)
    assert "INCOMPATIBLE_FUEL_CITED" not in page and "ACTIONABLE_SIGNAL" in page


def test_later_exclusion_or_buyer_conflict_is_never_silently_dropped_on_merge(tmp_path):
    import_opportunity(pre_rfp(tmp_path, buyer_type="OWNER"), tmp_path / "ws", now=NOW)
    second = json.loads((tmp_path / "hillcrest.json").read_text())
    second["opportunity_id"] = "hillcrest-2"
    second["buyer_type"] = "RERENTER"
    path = tmp_path / "second.json"
    path.write_text(json.dumps(second), encoding="utf-8")
    import_opportunity(path, tmp_path / "ws", now=NOW)
    manifest = json.loads((tmp_path / "ws" / "workspace.json").read_text())
    assert len(manifest["opportunities"]) == 1
    assert manifest["opportunities"][0]["buyer_type"] == "RERENTER"
    assert "buyer_type" in manifest["opportunities"][0]["buyer_conflicts"]
    assert "EXCLUDED_BUYER" in _page(tmp_path)


def test_merged_requirement_is_not_also_listed_unknown(tmp_path):
    def no_fuel(item, ref):
        item["requirements"].pop("fuel", None)
    import_opportunity(_edit(tmp_path, no_fuel), tmp_path / "ws", now=NOW)
    second = json.loads((tmp_path / "hillcrest.json").read_text())
    second["opportunity_id"] = "hillcrest-fuel"
    second["requirements"]["fuel"] = "natural gas"
    second["requirement_quotes"]["fuel"] = {"capture_file": second["sources"][0]["capture_file"],
                                            "quote": "temporary construction power"}
    path = tmp_path / "fuel.json"
    path.write_text(json.dumps(second), encoding="utf-8")
    import_opportunity(path, tmp_path / "ws", now=NOW)
    page = _page(tmp_path)
    assert "VERIFIED</span> requirements.fuel" in page
    assert "UNKNOWN</span> requirements.fuel" not in page


def test_invalid_buyer_type_writes_nothing_to_the_workspace(tmp_path):
    with pytest.raises(ValueError, match="buyer_type"):
        import_opportunity(pre_rfp(tmp_path, buyer_type="friend"), tmp_path / "ws", now=NOW)
    assert not (tmp_path / "ws" / "captures").exists()
