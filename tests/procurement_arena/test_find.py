"""Find tab: lead store, heuristic classifier, background search/capture flow, and its HTTP boundary.

No network and no real Firecrawl: the search and scrape functions are replaced with local fakes.
"""
from __future__ import annotations

import http.client
import json
import threading
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from athena_procurement_arena import firecrawl_discovery, local_ui
from athena_procurement_arena.leads import LeadStore, classify, lead_id_for, normalize_url
from athena_procurement_arena.public_capture import capture_markdown, write_capture

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "config/discovery.catalog.json"
NOW = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)


# ----- URL identity -----
@pytest.mark.parametrize("raw,expected", [
    ("HTTPS://Example.COM/Path/", "https://example.com/Path"),
    ("https://example.com/a?utm_source=x&id=7&gclid=1&fbclid=2#frag", "https://example.com/a?id=7"),
    ("https://example.com/", "https://example.com"),
    ("https://example.com:443/a/", "https://example.com/a"),
    ("http://example.com:8080/a", "http://example.com:8080/a"),
    ("https://example.com/a?UTM_Campaign=z", "https://example.com/a"),
])
def test_normalize_url(raw, expected):
    assert normalize_url(raw) == expected


def test_equivalent_urls_share_one_id_and_private_urls_are_rejected():
    ids = {lead_id_for(normalize_url(u)) for u in (
        "https://Example.com/rfp/", "https://example.com/rfp#top", "https://example.com/rfp?utm_medium=email")}
    assert len(ids) == 1 and len(next(iter(ids))) == 16
    for bad in ("http://localhost/x", "http://127.0.0.1/x", "ftp://example.com/x", "javascript:alert(1)",
                "https://user:pw@example.com/x"):
        with pytest.raises(ValueError):
            normalize_url(bad)


# ----- classifier -----
def test_classifier_rfp_project_other_and_keywords():
    rfp = classify("Request for Proposals: temporary power generation", "50 MW bridge power generators",
                   "https://county.example.gov/bids/temp-power")
    assert rfp.kind == "RFP"
    assert {"request for proposal", "rfp"} & set(rfp.rfp) == {"request for proposal"}
    assert {"temporary power", "bridge power", "generator", "MW"} <= set(rfp.power)
    portal = classify("Notice", "", "https://www.bidnetdirect.com/x")
    assert portal.kind == "RFP" and portal.rfp == ("host:bidnetdirect.com",)
    assert classify("IFB 22-04 Substation work", "", "https://a.example/x").kind == "RFP"
    project = classify("Data center campus announced", "Planned substation and 300 megawatts of load",
                       "https://news.example/story")
    assert project.kind == "PROJECT"
    assert {"data center", "announced", "planned", "substation"} <= set(project.project)
    assert {"megawatt", "substation", "load"} <= set(project.power)
    other = classify("Best pizza in town", "Great reviews", "https://food.example/menu")
    assert (other.kind, other.rfp, other.project, other.power) == ("OTHER", (), (), ())
    # word boundaries: no match inside other words
    assert classify("Download the bidding guide", "", "https://a.example/").kind == "OTHER"
    assert classify("", "", "https://a.example/request-for-proposal-2026").kind == "RFP"
    assert classify("x", "x", "https://notsam.gov.evil.example/").rfp == ()


# ----- store -----
def test_store_upsert_never_resurrects_dismissed_and_merges_queries(tmp_path):
    store = LeadStore(tmp_path / "leads.sqlite3")
    lead_id, is_new = store.upsert_hit("https://example.com/rfp/", "RFP one", "snippet", "web", "q1", NOW)
    assert is_new
    same_id, again = store.upsert_hit("https://EXAMPLE.com/rfp?utm_source=a", "", "", "news", "q2",
                                      NOW + timedelta(days=1))
    assert (same_id, again) == (lead_id, False)
    lead = store.get(lead_id)
    assert lead["query_ids"] == ["q1", "q2"] and lead["title"] == "RFP one"
    assert lead["first_seen"] != lead["last_seen"] and lead["kind"] == "RFP"
    store.set_status(lead_id, "dismiss", now=NOW)
    store.upsert_hit("https://example.com/rfp", "RFP one", "snippet", "web", "q3", NOW + timedelta(days=2))
    assert store.get(lead_id)["status"] == "DISMISSED"
    assert store.get(lead_id)["query_ids"] == ["q1", "q2", "q3"]
    assert store.set_status(lead_id, "restore")["status"] == "NEW"


def test_store_snooze_expiry_filters_and_counts(tmp_path):
    store = LeadStore(tmp_path / "leads.sqlite3")
    a, _ = store.upsert_hit("https://example.com/a", "Solicitation A", "", "web", "q", NOW)
    b, _ = store.upsert_hit("https://example.com/b", "Pipeline construction announced", "", "web", "q", NOW)
    store.upsert_hit("https://example.com/c", "Nothing relevant", "100% pure_water", "web", "q", NOW)
    store.set_status(a, "snooze", days=3, now=NOW)
    assert store.get(a, NOW + timedelta(days=2))["status"] == "SNOOZED"
    assert store.get(a, NOW + timedelta(days=4))["status"] == "NEW"  # snooze expired
    assert {x["id"] for x in store.leads(kind="RFP")} == {a}
    assert {x["id"] for x in store.leads(text="PIPELINE")} == {b}
    assert len(store.leads(text="%")) == 1 and store.leads(text="p_re") == []  # LIKE wildcards are escaped
    counts = store.counts()
    assert counts["matrix"]["RFP"]["NEW"] == 1 and counts["by_status"]["NEW"] == 3 and counts["total"] == 3
    with pytest.raises(ValueError):
        store.leads(kind="BOGUS")
    with pytest.raises(ValueError):
        store.set_status(a, "snooze", days=0)
    with pytest.raises(ValueError):
        store.set_status(a, "snooze", days=True)
    with pytest.raises(LookupError):
        store.set_status("0" * 16, "dismiss")


def test_store_captured_lead_restores_to_captured_and_runs_are_recorded(tmp_path):
    store = LeadStore(tmp_path / "leads.sqlite3")
    lead_id, _ = store.upsert_hit("https://example.com/a", "T", "", "web", "q", NOW)
    store.mark_captured(lead_id, "cap-1", "acquisition/captures/cap-1.capture.json", "ab" * 32, NOW.isoformat())
    with pytest.raises(LookupError):
        store.mark_captured(lead_id, "cap-2", "x", "y", "z")
    assert store.get(lead_id)["capture"]["capture_id"] == "cap-1"
    store.set_status(lead_id, "dismiss")
    assert store.set_status(lead_id, "restore")["status"] == "CAPTURED"
    store.start_run("r1", "q", "query text", NOW)
    assert store.last_run() is None
    store.finish_run("r1", 4, 3, None, NOW)
    assert store.last_run()["finished_at"].startswith("2026-10-22")
    assert store.runs()[0]["hit_count"] == 4


# ----- HTTP flow -----
@contextmanager
def serving(root, catalog=CATALOG):
    app = local_ui.Workbench(root, [], [])
    app.find.set_catalog(catalog)
    server = local_ui.WorkbenchServer(app, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        app.find.join(10)
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        app.close()


def call(server, path, data=None, *, token=True, raw=None, headers=None, method=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
    payload = json.dumps(data).encode() if data is not None else raw
    sent = {"Host": server.authority}
    if payload is not None:
        sent["Content-Type"] = "application/json"
        if token:
            sent["X-Trailforge-Token"] = server.workbench.token
    sent.update(headers or {})
    connection.request(method or ("POST" if payload is not None else "GET"), path, payload, sent)
    response = connection.getresponse()
    body = response.read()
    kind = response.getheader("Content-Type", "")
    result = (response.status, dict(response.getheaders()), json.loads(body) if kind.startswith("application/json") else body)
    connection.close()
    return result


def fake_search(hits_by_query, *, fail=(), gate=None, calls=None):
    def search(query, *, search_id, output_dir, limit, sources, categories, domains):
        if calls is not None:
            calls.append({"query": query, "search_id": search_id, "limit": limit, "sources": sources, "domains": domains})
        if gate is not None:
            assert gate.wait(10)
        for text, error in fail:
            if text in query:
                raise RuntimeError(error)
        hits = hits_by_query.get(query, [])
        path = Path(output_dir) / f"{search_id}-1.search.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"hits": [{"url": u, "title": t, "description": d, "source_type": "web"}
                                             for u, t, d in hits]}), encoding="utf-8")
        return {"search_id": search_id, "queries": [{"path": str(path), "hit_count": len(hits), "query": query}],
                "total_hits": len(hits)}
    return search


def finish(server):
    server.workbench.find.join(10)
    status, _, body = call(server, "/api/find/status")
    assert status == 200
    return body


XSS = '<img src=x onerror=alert(1)>"\'</script>'
Q1, Q2 = "temporary generation RFP temporary power procurement", "data center project power utility substation construction"


def test_run_flow_partial_failure_dedupe_and_verbatim_untrusted_text(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(firecrawl_discovery, "search", fake_search({
        Q1: [("https://example.com/rfp/1?utm_source=a", XSS, "Request for proposals, 20 MW generators"),
             ("https://example.com/shared", "Shared page", "Data center announced")],
        Q2: [("https://example.com/shared#x", "Shared page", "Data center announced")],
    }, fail=[("oil gas project", "Firecrawl search failed with exit code 1")], calls=calls))
    with serving(tmp_path) as server:
        status, _, state = call(server, "/api/find/state")
        assert status == 200 and len(state["catalog"]) == 13 and state["limits"]["max_results"] == 10
        assert state["run"] == {"state": "idle"} and state["counts"]["total"] == 0
        status, _, body = call(server, "/api/find/run", {
            "query_ids": ["temporary-generation-rfp", "data-center-projects", "oil-gas-projects"], "limit": 5})
        assert status == 202 and body["run"]["state"] == "running" and body["run"]["total"] == 3
        run = finish(server)["run"]
        assert run["state"] == "finished" and run["done"] == 3 and run["new_leads"] == 2
        assert [e["query"] for e in run["errors"]] == ["oil-gas-projects"]
        assert "exit code 1" in run["errors"][0]["error"] and "firecrawl" in run["errors"][0]["error"].lower()
        assert all(c["limit"] <= 5 and c["domains"] == () for c in calls) and len(calls) == 3
        assert len({c["search_id"] for c in calls}) == 3  # unique ids: artifacts are write-new-only
        assert (tmp_path / "acquisition" / "searches").is_dir()
        _, _, listing = call(server, "/api/find/leads?kind=RFP&status=NEW")
        [lead] = listing["leads"]
        assert lead["title"] == XSS and lead["url"] == "https://example.com/rfp/1"
        assert lead["kind"] == "RFP" and lead["query_ids"] == ["temporary-generation-rfp"]
        assert "request for proposal" in lead["matched"]["rfp"] and "generator" in lead["matched"]["power"]
        _, _, shared = call(server, "/api/find/leads?q=shared")
        assert shared["leads"][0]["query_ids"] == ["data-center-projects", "temporary-generation-rfp"]
        assert shared["leads"][0]["kind"] == "PROJECT"
        assert call(server, f"/api/find/leads/{lead['id']}")[2]["lead"]["title"] == XSS
        assert call(server, "/api/find/leads?status=BOGUS")[0] == 400
        assert finish(server)["last_run"]["queries"] == 3


def test_second_run_is_409_and_custom_query_defaults(tmp_path, monkeypatch):
    gate, calls = threading.Event(), []
    monkeypatch.setattr(firecrawl_discovery, "search", fake_search({}, gate=gate, calls=calls))
    with serving(tmp_path, catalog=None) as server:
        assert call(server, "/api/find/state")[2]["catalog"] == []
        status, _, body = call(server, "/api/find/run", {"query_ids": [], "custom": "  mobile gas turbine RFP  "})
        assert status == 202
        assert call(server, "/api/find/run", {"query_ids": [], "custom": "another"})[0] == 409
        assert call(server, "/api/find/status")[2]["run"]["state"] == "running"
        gate.set()
        assert finish(server)["run"]["state"] == "finished"
    assert calls[0]["query"] == "mobile gas turbine RFP" and calls[0]["limit"] == 10
    assert calls[0]["sources"] == ("web", "news")


def test_missing_firecrawl_is_a_clear_error_and_stops_the_run(tmp_path, monkeypatch):
    monkeypatch.setattr(firecrawl_discovery, "search", fake_search(
        {}, fail=[("", "Firecrawl CLI is not installed or not on PATH")]))
    with serving(tmp_path) as server:
        ids = ["temporary-generation-rfp", "data-center-projects"]
        assert call(server, "/api/find/run", {"query_ids": ids})[0] == 202
        run = finish(server)["run"]
    assert run["state"] == "finished" and run["done"] == 1 and len(run["errors"]) == 1
    assert "not installed" in run["errors"][0]["error"]


@pytest.mark.parametrize("body", [
    [], {"query_ids": "temporary-generation-rfp"}, {"query_ids": [1]}, {"query_ids": ["nope"]},
    {"query_ids": ["temporary-generation-rfp", "temporary-generation-rfp"]}, {"query_ids": []},
    {"query_ids": [], "custom": ""}, {"query_ids": [], "custom": "   "}, {"query_ids": [], "custom": "x" * 201},
    {"query_ids": [], "custom": "bad\x00text"}, {"query_ids": [], "custom": 5},
    {"query_ids": [], "custom": "--api-url=http://evil.example"}, {"query_ids": [], "custom": "-jobs temporary power"},
    {"query_ids": [], "custom": "  -x"},
    {"query_ids": ["data-center-projects"], "limit": 0}, {"query_ids": ["data-center-projects"], "limit": 11},
    {"query_ids": ["data-center-projects"], "limit": True}, {"query_ids": ["data-center-projects"], "limit": "5"},
    {"query_ids": ["data-center-projects"], "extra": 1},
])
def test_run_rejects_bad_bodies_without_calling_firecrawl(tmp_path, monkeypatch, body):
    def boom(*args, **kwargs):
        raise AssertionError("must not search")
    monkeypatch.setattr(firecrawl_discovery, "search", boom)
    with serving(tmp_path) as server:
        status, _, result = call(server, "/api/find/run", body)
        assert status == 400 and "error" in result
        assert call(server, "/api/find/status")[2]["run"] == {"state": "idle"}


def test_run_cap_is_the_catalog_size(tmp_path, monkeypatch):
    monkeypatch.setattr(firecrawl_discovery, "search", fake_search({}))
    with serving(tmp_path) as server:
        every = [q["id"] for q in call(server, "/api/find/state")[2]["catalog"]]
        assert call(server, "/api/find/run", {"query_ids": every + ["x"]})[0] == 400
        status, _, body = call(server, "/api/find/run", {"query_ids": every, "custom": "plus one"})
        assert status == 202 and body["run"]["total"] == 14
        finish(server)


def test_mutations_require_token_json_and_bounded_bodies(tmp_path, monkeypatch):
    monkeypatch.setattr(firecrawl_discovery, "search", fake_search({}))
    with serving(tmp_path) as server:
        lead_id = server.workbench.find.store.upsert_hit("https://example.com/a", "A", "", "web", "q")[0]
        for path, data in [("/api/find/run", {"query_ids": ["data-center-projects"]}),
                           (f"/api/find/leads/{lead_id}/status", {"action": "dismiss"}),
                           (f"/api/find/leads/{lead_id}/capture", {"reviewer": "me"})]:
            assert call(server, path, data, token=False)[0] == 403
            assert call(server, path, data, token=False, headers={"X-Trailforge-Token": "wrong"})[0] == 403
            assert call(server, path, data, headers={"Origin": "http://evil.example"})[0] == 403
            assert call(server, path, data, headers={"Content-Type": "text/plain"})[0] == 415
        assert server.workbench.find.store.get(lead_id)["status"] == "NEW"
        assert call(server, "/api/find/run", raw=b"x" * 4097)[0] == 400
        assert call(server, "/api/find/run", raw=b"{not json")[0] == 400
        assert call(server, "/api/find/run", raw=b'"string"')[0] == 400
        assert call(server, "/api/find/run", raw=b"{}", headers={"Content-Length": "2", "Transfer-Encoding": "chunked"})[0] == 400
        assert call(server, "/api/find/other", {"a": 1})[0] == 404
        assert call(server, "/api/find/leads/NOTANID/status", {"action": "dismiss"})[0] == 404
        for body in ({"action": "explode"}, {"action": "snooze"}, {"action": "snooze", "days": 400},
                     {"action": "snooze", "days": "7"}, {"action": 1}, {"action": "dismiss", "x": 1}, {}):
            assert call(server, f"/api/find/leads/{lead_id}/status", body)[0] == 400
        assert call(server, f"/api/find/leads/{'0' * 16}/status", {"action": "dismiss"})[0] == 404
        assert call(server, f"/api/find/leads/{lead_id}/capture", {"reviewer": ""})[0] == 400
        assert call(server, f"/api/find/leads/{lead_id}/capture", {"reviewer": "me", "x": 1})[0] == 400
        assert server.workbench.find.store.get(lead_id)["status"] == "NEW"


def test_triage_endpoints_and_dismissal_survives_a_new_search(tmp_path, monkeypatch):
    hit = ("https://example.com/rfp", "Solicitation", "temporary power")
    monkeypatch.setattr(firecrawl_discovery, "search", fake_search({Q1: [hit]}))
    with serving(tmp_path) as server:
        assert call(server, "/api/find/run", {"query_ids": ["temporary-generation-rfp"]})[0] == 202
        finish(server)
        [lead] = call(server, "/api/find/leads")[2]["leads"]
        path = f"/api/find/leads/{lead['id']}/status"
        assert call(server, path, {"action": "dismiss"})[2]["lead"]["status"] == "DISMISSED"
        assert call(server, "/api/find/leads?status=NEW")[2]["leads"] == []
        assert call(server, "/api/find/run", {"query_ids": ["temporary-generation-rfp"]})[0] == 202
        finish(server)
        assert call(server, f"/api/find/leads/{lead['id']}")[2]["lead"]["status"] == "DISMISSED"
        snoozed = call(server, path, {"action": "snooze", "days": 7})[2]["lead"]
        assert snoozed["status"] == "SNOOZED" and snoozed["snooze_until"]
        assert call(server, path, {"action": "restore"})[2]["lead"]["status"] == "NEW"
        assert call(server, "/api/find/status")[2]["counts"]["by_status"]["NEW"] == 1


def fake_scrape(calls=None, fail=None):
    def scrape(url, *, capture_id, captured_by, output_dir, source_type="web", query="", max_age_ms=0):
        if calls is not None:
            calls.append({"url": url, "capture_id": capture_id, "captured_by": captured_by, "max_age_ms": max_age_ms})
        if fail:
            raise RuntimeError(fail)
        capture = capture_markdown(url, "Solicitation 25-01 <script>alert(1)</script> needs 20 MW", capture_id=capture_id,
                                   captured_by=captured_by)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        path = Path(output_dir) / f"{capture_id}.capture.json"
        write_capture(capture, path)
        return capture, path, path.with_name(f"{capture_id}.acquisition.json")
    return scrape


def test_capture_flow_stores_reference_text_and_template(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(firecrawl_discovery, "scrape", fake_scrape(calls))
    with serving(tmp_path) as server:
        store = server.workbench.find.store
        lead_id = store.upsert_hit("https://example.com/solicitation", XSS, "RFP text", "web", "temporary-generation-rfp")[0]
        base = f"/api/find/leads/{lead_id}"
        assert call(server, base + "/capture")[0] == 404 and call(server, base + "/template")[0] == 404  # not captured
        status, _, body = call(server, base + "/capture", {"reviewer": "N. Operator"})
        assert status == 202 and body["capture"]["state"] == "running"
        assert finish(server)["captures"] == {}
        lead = call(server, base)[2]["lead"]
        assert lead["status"] == "CAPTURED" and lead["capture"]["capture_id"].startswith(f"lead-{lead_id}-")
        assert lead["capture"]["path"].startswith("acquisition/captures/")
        assert calls[0]["max_age_ms"] == 0 and calls[0]["captured_by"] == "N. Operator"
        assert call(server, base + "/capture", {"reviewer": "x"})[0] == 409  # already captured
        status, _, text = call(server, base + "/capture")
        assert status == 200 and "<script>alert(1)</script>" in text["text"] and not text["truncated"]
        assert text["content_sha256"] == lead["capture"]["content_sha256"] and text["captured_at"]
        assert "not verified" in text["notice"]
        status, headers, template = call(server, base + "/template")
        assert status == 200 and "attachment" in headers["Content-Disposition"] and f"lead-{lead_id}" in headers["Content-Disposition"]
        assert template["schema_version"] == "trailforge-opportunity-input-v1"
        assert template["opportunity_id"] == f"lead-{lead_id}" and template["title"] is None  # no unreviewed facts
        assert template["_lead"]["search_title"] == XSS  # reference only, under an ignored key
        assert template["field_evidence"] == {} and template["requirement_quotes"] == {}
        assert template["kind"] is None and template["reviewed_by"] is None and template["reviewed_at"] is None
        assert set(template["requirements"].values()) == {None}
        assert set(template["identity"].values()) == {None}
        assert Path(template["sources"][0]["capture_file"]).is_file()
        assert "25-01" not in json.dumps(template) and "20 MW" not in json.dumps(template)  # capture facts not copied
        # the skeleton cannot be imported until a human fills it in
        from athena_procurement_arena.opportunity_workspace import import_opportunity
        (tmp_path / "in.json").write_text(json.dumps(template), encoding="utf-8")
        with pytest.raises(ValueError):
            import_opportunity(tmp_path / "in.json", tmp_path / "ws")


def test_capture_failure_is_reported_and_can_be_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(firecrawl_discovery, "scrape", fake_scrape(fail="Firecrawl scrape failed with exit code 2"))
    with serving(tmp_path) as server:
        lead_id = server.workbench.find.store.upsert_hit("https://example.com/p", "P", "", "web", "q")[0]
        base = f"/api/find/leads/{lead_id}"
        assert call(server, base + "/capture", {"reviewer": "me"})[0] == 202
        captures = finish(server)["captures"]
        assert captures[lead_id]["state"] == "failed" and "exit code 2" in captures[lead_id]["error"]
        assert call(server, base)[2]["lead"]["status"] == "NEW"
        monkeypatch.setattr(firecrawl_discovery, "scrape", fake_scrape())
        assert call(server, base + "/capture", {"reviewer": "me"})[0] == 202
        finish(server)
        assert call(server, base)[2]["lead"]["status"] == "CAPTURED"


def test_second_concurrent_capture_of_one_lead_is_409(tmp_path, monkeypatch):
    gate = threading.Event()
    inner = fake_scrape()

    def slow(*args, **kwargs):
        assert gate.wait(10)
        return inner(*args, **kwargs)
    monkeypatch.setattr(firecrawl_discovery, "scrape", slow)
    with serving(tmp_path) as server:
        store = server.workbench.find.store
        lead_id = store.upsert_hit("https://example.com/p", "P", "", "web", "q")[0]
        base = f"/api/find/leads/{lead_id}/capture"
        assert call(server, base, {"reviewer": "me"})[0] == 202
        assert call(server, base, {"reviewer": "me"})[0] == 409
        gate.set()
        finish(server)


def test_find_reads_do_not_wait_on_the_workbench_lock(tmp_path):
    with serving(tmp_path) as server:
        with server.workbench.lock:  # a long locked GET elsewhere must not stall polling
            assert call(server, "/api/find/status")[0] == 200
            assert call(server, "/api/find/leads")[0] == 200


def test_find_assets_and_navigation_are_served_without_inline_script_or_innerhtml(tmp_path):
    with serving(tmp_path) as server:
        status, headers, js = call(server, "/app/app_find.js")
        assert status == 200 and headers["Content-Type"].startswith("text/javascript")
        assert "script-src 'self'" in headers["Content-Security-Policy"]
        _, _, page = call(server, "/app")
        _, _, app_js = call(server, "/app/app.js")
        _, _, css = call(server, "/app/app.css")
    assert b'href="#/find"' in page and b"/app/app_find.js" in page and b"<script>" not in page
    assert b"innerHTML" not in js and b"insertAdjacentHTML" not in js and b"document.write" not in js
    assert b"Unreviewed leads from public web search. Nothing here is verified, contacted, or sent." in js
    assert b"noopener noreferrer" in js and b'"find"' in app_js and b".lead" in css
    for forbidden in (b"verified lead", b"Open RFP", b"open RFP"):
        assert forbidden not in js


def test_bad_catalog_is_reported_not_fatal(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    with serving(tmp_path / "wb", catalog=bad) as server:
        state = call(server, "/api/find/state")[2]
    assert state["catalog"] == [] and "could not be loaded" in state["catalog_error"]


def test_cli_catalog_option(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        local_ui.main(["--saved-only", "--experiments-dir", str(tmp_path), "--discovery-catalog", str(tmp_path / "missing.json")])
    assert "discovery catalog not found" in capsys.readouterr().err
    seen = {}

    class Stop(Exception):
        pass

    class FakeServer:
        def __init__(self, app, port):
            seen["catalog"] = dict(app.find.catalog)
            raise Stop

    monkeypatch.setattr(local_ui, "WorkbenchServer", FakeServer)
    monkeypatch.chdir(tmp_path)  # no config/discovery.catalog.json here: Find starts with custom queries only
    with pytest.raises(Stop):
        local_ui.main(["--saved-only", "--experiments-dir", str(tmp_path / "wb"), "--no-fixture-mining"])
    assert seen["catalog"] == {}
    with pytest.raises(Stop):
        local_ui.main(["--saved-only", "--experiments-dir", str(tmp_path / "wb2"), "--no-fixture-mining",
                       "--discovery-catalog", str(CATALOG)])
    assert len(seen["catalog"]) == 13


# ----- review fix loop -----
def gated_scrape(gate, calls=None):
    inner = fake_scrape(calls)

    def slow(*args, **kwargs):
        assert gate.wait(10)
        return inner(*args, **kwargs)
    return slow


def test_crashed_run_thread_never_leaves_the_run_stuck_in_running(tmp_path, monkeypatch):
    import sqlite3
    monkeypatch.setattr(firecrawl_discovery, "search", fake_search({}))
    with serving(tmp_path) as server:
        store = server.workbench.find.store
        original = store.start_run

        def boom(*args, **kwargs):
            raise sqlite3.OperationalError("database is locked")
        monkeypatch.setattr(store, "start_run", boom)
        assert call(server, "/api/find/run", {"query_ids": ["data-center-projects"]})[0] == 202
        run = finish(server)["run"]
        assert run["state"] == "finished" and run["finished_at"]
        assert run["errors"][0]["query"] == "run" and "locked" in run["errors"][0]["error"]
        monkeypatch.setattr(store, "start_run", original)
        assert call(server, "/api/find/run", {"query_ids": ["data-center-projects"]})[0] == 202  # not a stuck 409
        assert finish(server)["run"]["errors"] == []


def test_capture_finishing_after_a_dismissal_keeps_the_dismissal(tmp_path, monkeypatch):
    gate = threading.Event()
    monkeypatch.setattr(firecrawl_discovery, "scrape", gated_scrape(gate))
    with serving(tmp_path) as server:
        lead_id = server.workbench.find.store.upsert_hit("https://example.com/p", "P", "", "web", "q")[0]
        base = f"/api/find/leads/{lead_id}"
        assert call(server, base + "/capture", {"reviewer": "me"})[0] == 202
        assert call(server, base + "/status", {"action": "dismiss"})[2]["lead"]["status"] == "DISMISSED"
        gate.set()
        finish(server)
        lead = call(server, base)[2]["lead"]
        assert lead["status"] == "DISMISSED" and lead["capture"]["capture_id"]  # decision kept, ref saved
        assert call(server, base + "/status", {"action": "restore"})[2]["lead"]["status"] == "CAPTURED"


def test_snoozed_lead_captured_while_snoozed_stays_snoozed_until_expiry(tmp_path):
    store = LeadStore(tmp_path / "leads.sqlite3")
    lead_id, _ = store.upsert_hit("https://example.com/a", "T", "", "web", "q", NOW)
    store.set_status(lead_id, "snooze", days=3, now=NOW)
    store.mark_captured(lead_id, "cap", "acquisition/captures/cap.capture.json", "ab" * 32, NOW.isoformat())
    assert store.get(lead_id, NOW + timedelta(days=1))["status"] == "SNOOZED"
    assert store.get(lead_id, NOW + timedelta(days=4))["status"] == "CAPTURED"


def test_search_command_ends_options_before_the_query(tmp_path, monkeypatch):
    import subprocess
    seen = []

    def run(command, **kwargs):
        seen.append(command)
        Path(command[command.index("-o") + 1]).write_text(json.dumps({"success": True, "data": {"web": []}}))
        return subprocess.CompletedProcess(command, 0, "", "")
    monkeypatch.setattr(firecrawl_discovery, "_cli", lambda: ["node", "firecrawl.js"])
    monkeypatch.setattr(firecrawl_discovery.subprocess, "run", run)
    firecrawl_discovery.search("--api-url=http://evil.example", search_id="safe-id", output_dir=tmp_path)
    assert seen[0][-2:] == ["--", "--api-url=http://evil.example"]


def test_filled_in_template_imports_and_unknown_keys_are_ignored(tmp_path, monkeypatch):
    from athena_procurement_arena.opportunity_workspace import import_opportunity
    monkeypatch.setattr(firecrawl_discovery, "scrape", fake_scrape())
    with serving(tmp_path / "wb") as server:
        lead_id = server.workbench.find.store.upsert_hit("https://example.com/p", XSS, "", "web", "q")[0]
        assert call(server, f"/api/find/leads/{lead_id}/capture", {"reviewer": "me"})[0] == 202
        finish(server)
        template = call(server, f"/api/find/leads/{lead_id}/template")[2]
    assert "_instructions" in template and "_lead" in template
    template.update(kind="PRE_RFP_PROJECT", reviewed_by="Reviewer", reviewed_at="2026-10-22T12:00:00Z")
    (tmp_path / "in.json").write_text(json.dumps(template), encoding="utf-8")
    record = import_opportunity(tmp_path / "in.json", tmp_path / "ws")
    assert record["title"] is None and record["field_evidence"] == {}


def test_failing_domain_keeps_hits_from_domains_that_succeeded(tmp_path, monkeypatch):
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"schema_version": "trailforge-discovery-catalog-v1", "queries": [
        {"id": "multi", "query": "multi query", "domains": ["a.example", "b.example", "c.example"],
         "sources": ["web"], "limit": 10}]}), encoding="utf-8")
    seen = []

    def search(query, *, search_id, output_dir, limit, sources, categories, domains):
        seen.append((domains, search_id))
        if domains == ("b.example",):
            raise RuntimeError("Firecrawl search failed with exit code 1")
        path = Path(output_dir) / f"{search_id}-1.search.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        host = domains[0]
        path.write_text(json.dumps({"hits": [{"url": f"https://{host}/rfp", "title": f"RFP {host}",
                                               "description": "", "source_type": "web"}]}), encoding="utf-8")
        return {"queries": [{"path": str(path)}]}
    monkeypatch.setattr(firecrawl_discovery, "search", search)
    with serving(tmp_path / "wb", catalog=catalog) as server:
        status, _, body = call(server, "/api/find/run", {"query_ids": ["multi"]})
        assert status == 202 and body["run"]["total"] == 3
        run = finish(server)["run"]
        leads = call(server, "/api/find/leads")[2]["leads"]
    assert [d for d, _ in seen] == [("a.example",), ("b.example",), ("c.example",)]
    assert len({s for _, s in seen}) == 3
    assert run["done"] == 3 and run["new_leads"] == 2
    assert [e["query"] for e in run["errors"]] == ["multi (b.example)"]
    assert {lead["host"] for lead in leads} == {"a.example", "c.example"}


def test_non_public_hits_are_skipped_and_the_original_url_is_used_for_link_and_scrape(tmp_path, monkeypatch):
    original = "https://Example.com/ok/?utm_source=a#frag"
    monkeypatch.setattr(firecrawl_discovery, "search", fake_search({Q1: [
        ("http://127.0.0.1/x", "Local", "rfp"), ("http://localhost/y", "Local", "rfp"), (original, "Ok", "RFP")]}))
    scrapes = []
    monkeypatch.setattr(firecrawl_discovery, "scrape", fake_scrape(scrapes))
    with serving(tmp_path) as server:
        assert call(server, "/api/find/run", {"query_ids": ["temporary-generation-rfp"]})[0] == 202
        run = finish(server)["run"]
        [lead] = call(server, "/api/find/leads")[2]["leads"]
        assert run["errors"] == [] and run["seen_hits"] == 1
        assert lead["url"] == "https://example.com/ok" and lead["original_url"] == original
        assert call(server, f"/api/find/leads/{lead['id']}/capture", {"reviewer": "me"})[0] == 202
        finish(server)
    assert scrapes[0]["url"] == original


def test_tampered_capture_reference_is_rejected(tmp_path, monkeypatch):
    import sqlite3
    monkeypatch.setattr(firecrawl_discovery, "scrape", fake_scrape())
    with serving(tmp_path) as server:
        store = server.workbench.find.store
        lead_id = store.upsert_hit("https://example.com/p", "P", "", "web", "q")[0]
        base = f"/api/find/leads/{lead_id}"
        assert call(server, base + "/capture", {"reviewer": "me"})[0] == 202
        finish(server)
        assert call(server, base + "/capture")[0] == 200
        good_path = call(server, base)[2]["lead"]["capture"]["path"]
        (tmp_path / "outside.capture.json").write_text("{}", encoding="utf-8")
        for value in ("../outside.capture.json", "acquisition/captures/../../outside.capture.json",
                      str(tmp_path / "outside.capture.json")):
            with sqlite3.connect(store.path) as conn:
                conn.execute("UPDATE leads SET capture_path = ? WHERE id = ?", (value, lead_id))
            assert call(server, base + "/capture")[0] == 400
            assert call(server, base + "/template")[0] == 400
        with sqlite3.connect(store.path) as conn:  # valid path again, but the recorded hash no longer matches
            conn.execute("UPDATE leads SET capture_path = ?, capture_sha256 = ? WHERE id = ?",
                         (good_path, "ff" * 32, lead_id))
        assert call(server, base + "/capture")[0] == 400


def test_snooze_expiry_restore_and_dismiss_of_captured_over_http(tmp_path, monkeypatch):
    monkeypatch.setattr(firecrawl_discovery, "scrape", fake_scrape())
    with serving(tmp_path) as server:
        store = server.workbench.find.store
        expired = store.upsert_hit("https://example.com/expired", "A", "", "web", "q")[0]
        store.set_status(expired, "snooze", days=1, now=datetime.now(UTC) - timedelta(days=10))
        assert call(server, f"/api/find/leads/{expired}")[2]["lead"]["status"] == "NEW"
        assert [x["id"] for x in call(server, "/api/find/leads?status=NEW")[2]["leads"]] == [expired]
        snoozed = store.upsert_hit("https://example.com/snoozed", "B", "", "web", "q")[0]
        path = f"/api/find/leads/{snoozed}/status"
        assert call(server, path, {"action": "snooze", "days": 7})[2]["lead"]["status"] == "SNOOZED"
        assert [x["id"] for x in call(server, "/api/find/leads?status=SNOOZED")[2]["leads"]] == [snoozed]
        restored = call(server, path, {"action": "restore"})[2]["lead"]
        assert restored["status"] == "NEW" and restored["snooze_until"] is None
        captured = store.upsert_hit("https://example.com/captured", "C", "", "web", "q")[0]
        assert call(server, f"/api/find/leads/{captured}/capture", {"reviewer": "me"})[0] == 202
        finish(server)
        assert call(server, f"/api/find/leads/{captured}")[2]["lead"]["status"] == "CAPTURED"
        dismissed = call(server, f"/api/find/leads/{captured}/status", {"action": "dismiss"})[2]["lead"]
        assert dismissed["status"] == "DISMISSED" and dismissed["capture"]  # reference survives
        assert call(server, "/api/find/leads?status=CAPTURED")[2]["leads"] == []


def test_find_state_paths_go_through_the_workbench_safe_path(tmp_path):
    from athena_procurement_arena.lead_search import FindService
    seen = []

    def safe(path):
        seen.append(path.name)
        return path
    service = FindService(tmp_path, safe)
    assert "leads.sqlite3" in seen
    service.store.upsert_hit("https://example.com/a", "A", "", "web", "q")
    assert service.store.path.name == "leads.sqlite3"
