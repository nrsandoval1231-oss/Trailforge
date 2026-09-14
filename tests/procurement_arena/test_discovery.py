import json
from pathlib import Path

import pytest

from athena_procurement_arena import load_bundle_mapping, screen_aura_rental_candidate
from athena_procurement_arena.capture import build_candidate_bundle
from athena_procurement_arena.discovery import (
    ReviewCandidate,
    SourceConfig,
    candidate_to_capture_request,
    load_sources,
    parse_source,
    triage_score,
)
from athena_procurement_arena.discovery.fetch import FetchError, FetchResult
from athena_procurement_arena.discovery.pipeline import discover, run_source

FIXTURE = Path(__file__).parent / "fixtures" / "sample-bids.html"

HTML_CONFIG = SourceConfig(
    source_id="test-city", name="Test City", url="https://example-city.gov/bids",
    kind="html_list", jurisdiction="US-TEST",
    selectors={
        "row": "table.bids tbody tr", "title": "td.title a", "url": "td.title a@href",
        "buyer": "td.department", "published": "td.posted@datetime",
        "closes": "td.due@datetime", "solicitation_number": "td.number",
        "summary": "td.description",
    },
)

JSON_CONFIG = SourceConfig(
    source_id="test-api", name="Test API", url="https://api.example.gov/v2/search",
    kind="json_api",
    selectors={"row": "opportunitiesData", "title": "title", "url": "uiLink",
               "buyer": "fullParentPathName", "published": "postedDate",
               "solicitation_number": "solicitationNumber", "summary": "description"},
)


class StubFetcher:
    """Stands in for network retrieval so parsing and ranking stay testable."""

    def __init__(self, body: str, *, fail: bool = False):
        self.body = body
        self.fail = fail
        self.calls: list[str] = []

    def fetch(self, url, *, headers=None, params=None, rate_limit_seconds=2.0):
        self.calls.append(url)
        if self.fail:
            raise FetchError("simulated outage")
        return FetchResult(url, 200, self.body.encode("utf-8"),
                           "2026-09-14T13:00:00+00:00", "text/html", cache_path=None)


def test_html_selectors_extract_rows_and_resolve_relative_urls():
    records = parse_source(HTML_CONFIG, FIXTURE.read_text(encoding="utf-8"))
    assert len(records) == 3
    assert records[0]["title"] == "Temporary Power for Substation Commissioning"
    assert records[0]["url"] == "https://example-city.gov/bids/2026-101"
    assert records[0]["published"] == "2026-09-02T09:00:00-05:00"


def test_json_api_selectors_walk_dotted_paths():
    payload = json.dumps({"opportunitiesData": [
        {"title": "Temporary generation for commissioning", "uiLink": "https://sam.gov/opp/1",
         "fullParentPathName": "DEPT", "postedDate": "2026-09-02",
         "solicitationNumber": "N-1", "description": "bridge power during energization"},
    ]})
    records = parse_source(JSON_CONFIG, payload)
    assert records[0]["title"] == "Temporary generation for commissioning"
    assert records[0]["url"] == "https://sam.gov/opp/1"


def test_missing_selector_yields_an_absent_field_not_a_guess():
    config = SourceConfig(
        source_id="sparse", name="Sparse", url="https://example-city.gov/bids",
        kind="html_list", selectors={"row": "table.bids tbody tr", "title": "td.title a",
                                     "buyer": "td.nonexistent"})
    records = parse_source(config, FIXTURE.read_text(encoding="utf-8"))
    assert records[0]["buyer"] == ""
    assert records[0]["summary"] == ""


def test_triage_ranks_planned_power_above_maintenance():
    planned = triage_score("Temporary power for substation commissioning, 750 kW natural gas")
    maintenance = triage_score("Annual generator maintenance services, preventive maintenance")
    unrelated = triage_score("Playground resurfacing")
    assert planned.band == "HIGH"
    assert planned.score > maintenance.score
    assert unrelated.score == 0
    assert "generator maintenance" in maintenance.penalized


def test_discover_ranks_and_filters_the_queue():
    result = discover((HTML_CONFIG,), fetcher=StubFetcher(FIXTURE.read_text(encoding="utf-8")))
    titles = [item["title"] for item in result["candidates"]]
    assert titles[0] == "Temporary Power for Substation Commissioning"
    assert "Playground Resurfacing" not in titles
    assert all(item["status"] == "AWAITING_REVIEW" for item in result["candidates"])


def test_one_failing_source_does_not_fail_the_sweep():
    good = HTML_CONFIG
    bad = SourceConfig(source_id="down", name="Down", url="https://down.example.gov/bids",
                       kind="html_list", selectors={"row": "tr"})
    html = FIXTURE.read_text(encoding="utf-8")

    class Selective(StubFetcher):
        def fetch(self, url, *, headers=None, params=None, rate_limit_seconds=2.0):
            if "down.example.gov" in url:
                raise FetchError("simulated outage")
            return super().fetch(url, headers=headers, params=params,
                                 rate_limit_seconds=rate_limit_seconds)

    result = discover((good, bad), fetcher=Selective(html))
    assert result["status"] == "PASS"
    assert result["errors"] == ["down"]
    assert result["count"] >= 1


def test_error_source_contributes_no_rows():
    outcome = run_source(HTML_CONFIG, StubFetcher("", fail=True))
    assert outcome.status == "ERROR"
    assert outcome.candidates == ()


def test_api_key_source_fails_closed_without_the_environment_variable(monkeypatch):
    config = SourceConfig(
        source_id="keyed", name="Keyed", url="https://api.example.gov/v2/search",
        kind="json_api", api_key_env="TEST_DISCOVERY_KEY",
        params={"api_key": "{api_key}"}, selectors={"row": "data"})
    monkeypatch.delenv("TEST_DISCOVERY_KEY", raising=False)
    outcome = run_source(config, StubFetcher("{}"))
    assert outcome.status == "ERROR"
    assert "TEST_DISCOVERY_KEY" in outcome.error


def _candidate():
    return ReviewCandidate(
        source_id="test-city", title="Temporary Power for Substation Commissioning",
        url="https://example-city.gov/bids/2026-101", retrieved_at="2026-09-14T13:00:00+00:00",
        buyer="Example City", published="2026-09-02T09:00:00-05:00",
        closes="2026-10-01T14:00:00-05:00", solicitation_number="PW-2026-101",
        summary="temporary generation of 750 kW during the interconnection delay")


def test_a_candidate_is_not_evidence_and_needs_a_named_reviewer():
    candidate = _candidate()
    assert candidate.as_dict()["status"] == "AWAITING_REVIEW"
    with pytest.raises(ValueError, match="verified_by"):
        candidate_to_capture_request(
            candidate, verified_by="  ", verification_notes="x",
            excerpt="text", fixture_id="GT-100")


def test_promoted_candidate_becomes_a_normal_fixture_without_inventing_capacity():
    """Promotion carries only what the reviewer read; capacity stays unfilled."""
    request = candidate_to_capture_request(
        _candidate(), verified_by="nick-2026-09-14",
        verification_notes="Bid page reviewed; states temporary commissioning load.",
        excerpt="Contractor shall furnish temporary generation of 750 kW.",
        fixture_id="GT-100")
    bundle = build_candidate_bundle(request)
    screen = screen_aura_rental_candidate(bundle.fixtures[0].scenario.evidence)
    assert screen.status.value == "NEEDS_REVIEW"
    assert screen.reason_codes == ("REQUIRED_CAPACITY_NOT_CAPTURED",)

    with_capacity = candidate_to_capture_request(
        _candidate(), verified_by="nick-2026-09-14",
        verification_notes="Bid page reviewed; 750 kW stated on page 3.",
        excerpt="Contractor shall furnish temporary generation of 750 kW.",
        fixture_id="GT-100", required_kw=750, fuel="natural gas")
    qualified = build_candidate_bundle(with_capacity)
    assert screen_aura_rental_candidate(
        qualified.fixtures[0].scenario.evidence).status.value == "QUALIFIED"
    assert load_bundle_mapping(json.loads(qualified.dumps())).fixtures[0].fixture_id == "GT-100"


def test_shipped_configs_are_valid_and_disabled_until_verified():
    configs = load_sources(Path("src/athena_procurement_arena/discovery/configs"))
    assert configs
    assert all(not item.enabled for item in configs), (
        "a shipped source must stay disabled until its selectors are verified live")


def test_non_https_and_bad_config_are_rejected():
    with pytest.raises(ValueError, match="https"):
        SourceConfig(source_id="x", name="X", url="http://insecure.gov/bids",
                     kind="html_list", selectors={"row": "tr"})
    with pytest.raises(ValueError, match="row"):
        SourceConfig(source_id="x", name="X", url="https://ok.gov/bids",
                     kind="html_list", selectors={})
