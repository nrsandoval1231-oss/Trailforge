"""Find tab classifier v2: golden real-world cases, explainer/energy-context gates, deadline hints, ranking and the
re-rank migration. Heuristics only: nothing here claims a lead is real, open, or verified.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from athena_procurement_arena.lead_classifier import CLASSIFIER_VERSION, classify, deadline_hint, deadline_status
from athena_procurement_arena.lead_search import FindService
from athena_procurement_arena.leads import LeadStore

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)
# Real search hits (titles/snippets/URLs as stored on the owner's catalog searches), frozen with the expected kind.
CASES = json.loads((Path(__file__).with_name("lead_ranking_cases.json")).read_text(encoding="utf-8"))
BY_NAME = {case["name"]: case for case in CASES}


def run(case):
    return classify(case["title"], case["snippet"], case["url"])


# ----- golden cases -----
@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_golden_real_cases_keep_their_expected_kind(case):
    found = run(case)
    if case["kind"] != "ANY":  # ANY = known-noise page whose kind is not worth freezing, only its rank tier
        assert found.kind == case["kind"], (found.kind, found.reason, found.explainer, found.score)
    if found.kind == "OTHER":
        assert found.reason  # every Other card can say why


def test_lipa_temporary_generation_pages_lead_the_rfp_list():
    real = {c["name"]: run(c) for c in CASES if c.get("source") != "synthetic" and run(c).kind == "RFP"}
    lipa = {n for n, c in BY_NAME.items() if c["tier"] == "lipa"}
    assert len(lipa) == 6
    # Recall rules surface wording-only RFPs (an official bid PDF, a procurement-office letter) that may legitimately
    # outscore the weakest LIPA page, so the LIPA pages must be in the top 8 and above every ordinary RFP page.
    ranked = sorted(real, key=lambda n: -real[n].score)
    assert lipa <= set(ranked[:8])
    ordinary = [real[n].score for n in real if n not in lipa and BY_NAME[n]["tier"] != "recall"]
    assert min(real[n].score for n in lipa) > max(ordinary)


def test_community_power_solicitation_pages_outrank_generic_rfp_pages():
    scores = {name: run(case).score for name, case in BY_NAME.items()}
    buyers = [n for n, c in BY_NAME.items() if c["tier"] == "buyer"]
    lows = [n for n, c in BY_NAME.items() if c["tier"] == "lowrfp"]
    assert len(buyers) == 3 and len(lows) == 3
    assert min(scores[n] for n in buyers) > max(scores[n] for n in lows)


def test_real_project_signals_outrank_utility_how_to_pages():
    scores = {name: run(case).score for name, case in BY_NAME.items()}
    top = {n for n, c in BY_NAME.items() if c["tier"] == "project"}
    second = {n for n, c in BY_NAME.items() if c["tier"] == "project2"}
    low = {n for n, c in BY_NAME.items() if c["tier"] == "lowproject"}
    assert min(scores[n] for n in top) > max(scores[n] for n in second | low)
    assert min(scores[n] for n in second) > max(scores[n] for n in low)


def test_matched_words_and_chips_are_reported_for_the_ui():
    found = run(BY_NAME["lipa-lightrfp"])
    matched = found.matched()
    assert {"rfp", "request for proposal", "host:lightrfp.com"} <= set(matched["rfp"])
    assert "temporary generation" in matched["power"] and matched["deadline_hint"]["date"] == "2026-10-30"
    assert matched["reason"] == ""
    guide = run(BY_NAME["substation-design-guide"]).matched()
    assert guide["explainer"] == ["guide"] and guide["reason"] == "explainer-like: guide"
    assert json.loads(json.dumps(matched)) == matched  # stored as JSON


# ----- explainer detection and its escape hatches -----
@pytest.mark.parametrize("title,label", [
    ("Glossary of Power Procurement Terms", "glossary"),
    ("What is a temporary power RFP?", "what is/are"),
    ("What's the difference between bridge power and backup power", "what is/are"),
    ("Temporary power: complete guide", "guide"),
    ("How to bid on utility solicitations", "how to"),
    ("Understanding generation solicitations", "understanding"),
    ("Power procurement best practices", "best practices"),
    ("Temporary Generation Market Size, Share, Trends 2034", "market report"),
    ("Utility RFP template for power purchase", "template"),
    ("Power Procurement FAQ", "faq"),
    ("Data center power infrastructure: 5 key parts", "key parts"),
    ("Colocated generation: benefits, risks and strategy", "benefits, risks"),
    ("Turnkey temporary power solutions", "vendor marketing"),
    ("Senate permitting bill for pipelines", "policy"),
])
def test_explainer_patterns_are_named_in_the_result(title, label):
    assert label in classify(title, "", "https://x.example/page").explainer


def test_explainer_url_path_and_reference_hosts_count():
    assert "guide" in classify("Temporary power", "", "https://x.example/blog/temporary-power-guide").explainer
    wiki = classify("Oil refinery expansion", "", "https://en.wikipedia.org/wiki/Oil_refinery")
    assert wiki.explainer == ("reference site: wikipedia.org",) and wiki.kind == "OTHER"


def test_explainer_is_demoted_unless_it_carries_a_strong_signal():
    snippet = "The utility issues this RFP for temporary generation"
    weak = classify("Temporary generation RFP guide", snippet, "https://blog.example/post")
    assert weak.kind == "OTHER" and weak.reason == "explainer-like: guide"
    portal = classify("Temporary generation RFP guide", snippet, "https://www.bidnetdirect.com/x")
    official = classify("Temporary generation RFP guide", snippet, "https://county.example.gov/x")
    deadline = classify("Temporary generation RFP guide", snippet + ". Proposals due 2026-12-01.",
                        "https://blog.example/post")
    phrase = classify("Temporary generation guide", "A request for proposals for temporary power",
                      "https://blog.example/post")
    assert [x.kind for x in (portal, official, deadline, phrase)] == ["RFP"] * 4
    assert all(x.explainer == ("guide",) for x in (portal, official, deadline, phrase))
    # a project explainer is rescued only by a stated size
    assert classify("Data center substation guide", "", "https://x.example/a").kind == "OTHER"
    assert classify("Data center substation guide", "A 300 MW campus", "https://x.example/a").kind == "PROJECT"


# ----- energy-context gate -----
def test_bare_rfp_words_without_energy_context_are_other_and_say_so():
    for title in ("Request for Proposal: temporary staffing", "Solicitations", "RFQ 22-04 janitorial services"):
        found = classify(title, "Vendors may respond.", "https://city.example.gov/bids")
        assert found.kind == "OTHER" and found.reason == "RFP wording but no energy or power context"
    # any of: a POWER word, a broader energy word, or an energy/utility host supplies the context
    assert classify("RFP: generators", "", "https://city.example.gov/bids").kind == "RFP"
    assert classify("RFP", "for electric service", "https://city.example.gov/bids").kind == "RFP"
    assert classify("Solicitations", "", "https://www.somepower.org/solicitations").kind == "RFP"
    assert classify("Solicitations", "", "https://www.lipower.org/procurement").kind == "RFP"
    assert classify("Solicitations", "", "https://www.dgs.ca.gov/procurement").kind == "OTHER"  # .gov alone: no context


def test_load_alone_is_not_power_relevance():
    found = classify("RFP for load testing software", "peak load", "https://x.example/rfp")
    assert found.power == () and found.kind == "OTHER"
    assert "large load" in classify("Large-load customers", "", "https://x.example/a").power


def test_permit_only_and_generic_project_words_need_context():
    permit = classify("Is a Permit Required?", "Permits are required for most building projects.",
                      "https://village.example.gov/permits")
    assert permit.kind == "OTHER" and permit.reason == "permit wording only, no project"
    plain = classify("Construction notice", "Road construction planned for May", "https://county.example.gov/n")
    assert plain.kind == "OTHER" and plain.reason == "project wording but no energy or power context"
    assert classify("Construction planned", "A new substation", "https://county.example.gov/n").kind == "PROJECT"
    assert classify("Pizza", "Great reviews", "https://food.example/menu").reason == "no RFP or project words matched"


# ----- deadline hints -----
@pytest.mark.parametrize("snippet,date_,words", [
    ("Proposals are due by 2026-10-30.", "2026-10-30", "due by 2026-10-30"),
    ("Submissions are due by 5 p.m. PT on October 30, 2026.", "2026-10-30", "due by 5 p.m. PT on October 30, 2026"),
    ("Deadline: Oct. 30, 2026", "2026-10-30", "Deadline: Oct. 30, 2026"),
    ("Responses closing 10/30/2026 at noon", "2026-10-30", "closing 10/30/2026"),
    ("RFP Submittal Deadline: September 30, 2026 at 5 p.m.", "2026-09-30", "Deadline: September 30, 2026"),
    ("Bids must be submitted by Sept 3rd, 2026", "2026-09-03", "submitted by Sept 3rd, 2026"),
])
def test_deadline_hint_parses_common_date_phrases(snippet, date_, words):
    hint = deadline_hint("Request for Proposals", snippet)
    assert (hint["date"], hint["text"]) == (date_, words)


def test_deadline_hint_needs_deadline_wording_and_a_real_date():
    assert deadline_hint("RFP released 2026-10-30", "") is None  # a date without deadline wording
    assert deadline_hint("RFP", "Due 2026-13-45") is None  # not a calendar date
    assert deadline_hint("RFP", "Deadline soon") is None
    assert deadline_hint("RFP", "Release Date: September 2, 2026 Submittal Deadline: September 30, 2026")["date"] \
        == "2026-09-30"  # the deadline word belongs to the date it precedes, not the earlier release date
    assert deadline_hint("Proposals due by September 17, 2026, at 4:00 PM", "also due by September 3, 2026")["date"] \
        == "2026-09-17"  # first hint wins
    assert deadline_hint("Due", "by 2026-10-30")["date"] == "2026-10-30"  # title + snippet are read together


def test_deadline_status_is_computed_against_an_injected_today():
    hint = {"text": "due 2026-10-30", "date": "2026-10-30"}
    assert deadline_status(hint, date(2026, 10, 22)) == "future"
    assert deadline_status(hint, date(2026, 10, 30)) == "future"  # a date today is not yet past
    assert deadline_status(hint, date(2026, 10, 31)) == "past"
    assert deadline_status({"text": "due ?", "date": None}, date(2026, 10, 22)) == "unknown"
    assert deadline_status(None, date(2026, 10, 22)) is None


def test_store_adds_deadline_status_at_read_time_only(tmp_path):
    store = LeadStore(tmp_path / "leads.sqlite3")
    lead_id, _ = store.upsert_hit("https://www.lightrfp.com/bid/1", "2026 Temporary Generation RFP",
                                  "Proposals are due by 2026-10-30.", "web", "q", NOW)
    store.upsert_hit("https://x.example/plain", "Temporary generation RFP", "No dates here", "web", "q", NOW)
    assert store.get(lead_id, NOW)["deadline_status"] == "future"
    assert store.get(lead_id, NOW + timedelta(days=9))["deadline_status"] == "past"
    listed = {x["id"]: x for x in store.leads(now=NOW + timedelta(days=9))}
    assert listed[lead_id]["deadline_status"] == "past"
    assert sum("deadline_status" in x for x in listed.values()) == 1  # leads without a hint have no field
    stored = sqlite3.connect(tmp_path / "leads.sqlite3").execute("SELECT matched FROM leads WHERE id = ?",
                                                                 (lead_id,)).fetchone()[0]
    assert "deadline_status" not in stored and json.loads(stored)["deadline_hint"]["date"] == "2026-10-30"


# ----- score and ordering -----
def test_score_weights_power_hosts_deadline_and_penalties():
    base = classify("Solicitation: power", "", "https://x.example/a")
    assert classify("Solicitation: temporary power", "", "https://x.example/a").score > base.score
    assert classify("Solicitation: substation power", "", "https://x.example/a").score > base.score
    strong = classify("Solicitation", "temporary power", "https://x.example/a").score
    medium = classify("Solicitation", "substation power", "https://x.example/a").score
    assert strong > medium > base.score
    gov = classify("Solicitation: power", "", "https://county.example.gov/a")
    assert gov.score == base.score + 8
    assert classify("Solicitation: power", "due 2026-12-01", "https://x.example/a").score == base.score + 8
    assert classify("Solicitation: power", "", "https://www.highergov.com/a").score == base.score + 8  # portal host
    assert classify("Solicitation: power", "", "https://cs.example.edu/a").score == base.score - 4
    # official hosts from the discovery catalog count like .gov
    assert classify("Solicitation: power", "", "https://buyer.example.org/a", ("buyer.example.org",)).score \
        == base.score + 8
    # only city/county/state style .us hosts are official, not any .us name
    assert classify("Solicitation: power", "", "https://ci.town.tx.us/a").score == base.score + 8
    assert classify("Solicitation: power", "", "https://company.us/a").score == base.score
    guide = classify("Solicitation: power guide", "", "https://x.example/a")
    assert guide.kind == "OTHER" and guide.score == -10  # demoted: loses the RFP bonus and takes the penalty
    social = classify("Gas compressor station planned", "", "https://www.reddit.com/r/x")
    assert social.kind == "PROJECT" and social.score == classify("Gas compressor station planned", "",
                                                                 "https://x.example/r").score - 8


def test_leads_sort_by_score_then_last_seen(tmp_path):
    store = LeadStore(tmp_path / "leads.sqlite3")
    low, _ = store.upsert_hit("https://x.example/low", "Solicitation: power", "", "web", "q", NOW)
    high, _ = store.upsert_hit("https://x.example/high", "Solicitation: temporary power", "", "web", "q", NOW)
    tie_old, _ = store.upsert_hit("https://x.example/tie-old", "Solicitation: grid", "", "web", "q", NOW)
    tie_new, _ = store.upsert_hit("https://x.example/tie-new", "Solicitation: grid", "", "web", "q",
                                  NOW + timedelta(days=1))
    # last_seen, not first_seen, breaks ties: seeing tie_old again later moves it ahead of tie_new
    assert [x["id"] for x in store.leads(kind="RFP")] == [high, tie_new, tie_old, low]
    store.upsert_hit("https://x.example/tie-old", "", "", "web", "q2", NOW + timedelta(days=2))
    assert [x["id"] for x in store.leads(kind="RFP")] == [high, tie_old, tie_new, low]


# ----- re-rank migration -----
OLD_SCHEMA = """
CREATE TABLE leads (
  id TEXT PRIMARY KEY, url TEXT NOT NULL, title TEXT NOT NULL, snippet TEXT NOT NULL, source_type TEXT NOT NULL,
  query_ids TEXT NOT NULL, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('NEW','DISMISSED','SNOOZED','CAPTURED')), snooze_until TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('RFP','PROJECT','OTHER')), matched TEXT NOT NULL, score INTEGER NOT NULL,
  capture_id TEXT, capture_path TEXT, capture_sha256 TEXT, captured_at TEXT);
CREATE INDEX leads_status_kind ON leads (status, kind);
CREATE TABLE search_runs (
  run_id TEXT PRIMARY KEY, query_id TEXT NOT NULL, query_text TEXT NOT NULL, started_at TEXT NOT NULL,
  finished_at TEXT, hit_count INTEGER NOT NULL DEFAULT 0, new_count INTEGER NOT NULL DEFAULT 0, error TEXT);
"""
OLD_ROWS = [  # id, title, snippet, url, status, snooze_until, capture
    ("a" * 16, "Glossary of Procurement Terms", "A RFP is a solicitation.", "https://gwu.example.edu/glossary",
     "DISMISSED", None, None),
    ("b" * 16, "2026 Temporary Generation RFP", "Proposals are due by 2026-10-30.", "https://www.lightrfp.com/b/1",
     "CAPTURED", None, ("cap-1", "acquisition/captures/cap-1.capture.json", "ab" * 32, "2026-10-01T00:00:00+00:00")),
    ("c" * 16, "Transco Gas Compressor Station", "A 69,000 KV substation generator.", "https://c.example/p",
     "SNOOZED", "2026-12-01T00:00:00+00:00", None),
    ("d" * 16, "Thinking about a home project?", "Electrical permits are required.", "https://d.example/p",
     "NEW", None, None),
]


def make_old_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(OLD_SCHEMA)
    for lead_id, title, snippet, url, status, until, cap in OLD_ROWS:
        conn.execute(
            "INSERT INTO leads VALUES (?, ?, ?, ?, 'web', '[\"q1\"]', '2026-09-01T00:00:00+00:00',"
            " '2026-09-02T00:00:00+00:00', ?, ?, 'RFP', '{\"rfp\": [\"rfp\"], \"project\": [], \"power\": [\"load\"]}',"
            " 1, ?, ?, ?, ?)", (lead_id, url, title, snippet, status, until, *(cap or (None,) * 4)))
    conn.commit()
    conn.close()


def snapshot(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM leads ORDER BY id").fetchall()
    return [dict(row) for row in rows]


PRESERVED = ("id", "url", "title", "snippet", "source_type", "query_ids", "first_seen", "last_seen", "status",
             "snooze_until", "capture_id", "capture_path", "capture_sha256", "captured_at")


def test_old_database_is_reranked_once_and_operator_state_is_untouched(tmp_path):
    path = tmp_path / "leads.sqlite3"
    make_old_db(path)
    before = snapshot(path)
    store = LeadStore(path)
    store.counts()  # first use opens the store and re-ranks
    after = snapshot(path)
    for old, new in zip(before, after, strict=True):
        assert {k: old[k] for k in PRESERVED} == {k: new[k] for k in PRESERVED}  # nothing operator-owned changes
    by_id = {row["id"]: row for row in after}
    assert by_id["a" * 16]["kind"] == "OTHER" and json.loads(by_id["a" * 16]["matched"])["explainer"] == ["glossary"]
    assert by_id["a" * 16]["status"] == "DISMISSED"
    assert by_id["b" * 16]["kind"] == "RFP" and by_id["b" * 16]["status"] == "CAPTURED"
    assert by_id["b" * 16]["capture_id"] == "cap-1" and by_id["b" * 16]["capture_sha256"] == "ab" * 32
    assert by_id["c" * 16]["kind"] == "PROJECT" and by_id["c" * 16]["status"] == "SNOOZED"
    assert by_id["c" * 16]["snooze_until"] == "2026-12-01T00:00:00+00:00"
    assert by_id["d" * 16]["kind"] == "OTHER" and by_id["d" * 16]["score"] == 0  # permit wording only, no power words
    assert json.loads(by_id["d" * 16]["matched"])["reason"] == "permit wording only, no project"
    assert by_id["b" * 16]["score"] > by_id["c" * 16]["score"] > by_id["a" * 16]["score"]
    assert "original_url" in after[0]  # the older schema also gained its missing column
    meta = sqlite3.connect(path).execute("SELECT value FROM meta WHERE key = 'classifier_version'").fetchone()
    assert meta[0] == str(CLASSIFIER_VERSION)
    # the dismissed explainer stays dismissed and is still listable; sorting uses the new scores
    assert store.get("a" * 16)["status"] == "DISMISSED"
    assert [x["id"] for x in store.leads(kind="RFP")] == ["b" * 16]


def test_rerank_is_idempotent_and_reruns_only_when_the_version_differs(tmp_path):
    path = tmp_path / "leads.sqlite3"
    make_old_db(path)
    LeadStore(path).counts()
    first = snapshot(path)
    LeadStore(path).counts()  # same version: a second open changes nothing
    assert snapshot(path) == first
    # tamper a derived column and keep the version: it is NOT recomputed
    conn = sqlite3.connect(path)
    conn.execute("UPDATE leads SET score = 999 WHERE id = ?", ("a" * 16,))
    conn.commit()
    LeadStore(path).counts()
    assert snapshot(path)[0]["score"] == 999
    # an older stored version triggers exactly one re-run that repairs it
    conn.execute("UPDATE meta SET value = '1' WHERE key = 'classifier_version'")
    conn.commit()
    conn.close()
    LeadStore(path).counts()
    assert snapshot(path) == first


def test_rerank_rolls_back_as_a_whole_if_it_is_interrupted(tmp_path, monkeypatch):
    path = tmp_path / "leads.sqlite3"
    make_old_db(path)
    before = snapshot(path)
    store = LeadStore(path)
    calls = []
    real = store._classify

    def interrupted(title, snippet, url):
        calls.append(url)
        if len(calls) == 3:
            raise KeyboardInterrupt  # not an Exception: the whole transaction must roll back
        return real(title, snippet, url)

    monkeypatch.setattr(store, "_classify", interrupted)
    with pytest.raises(KeyboardInterrupt):
        store.counts()
    # no half-ranked database (the schema upgrade itself, adding original_url, is not part of the re-rank)
    assert [{k: row[k] for k in before[0]} for row in snapshot(path)] == before
    monkeypatch.setattr(store, "_classify", real)
    store.counts()
    assert snapshot(path)[0]["kind"] == "OTHER"


def test_one_row_that_breaks_the_classifier_does_not_lock_the_tab(tmp_path, monkeypatch):
    path = tmp_path / "leads.sqlite3"
    make_old_db(path)
    before = {row["id"]: row for row in snapshot(path)}
    store = LeadStore(path)
    real = store._classify

    def poisoned(title, snippet, url):
        if "home project" in title:
            raise ValueError("cannot classify this row")
        return real(title, snippet, url)

    monkeypatch.setattr(store, "_classify", poisoned)
    assert store.counts()["total"] == 4  # opens fine
    after = {row["id"]: row for row in snapshot(path)}
    bad = after["d" * 16]
    assert (bad["kind"], bad["matched"], bad["score"]) == (before["d" * 16]["kind"], before["d" * 16]["matched"],
                                                           before["d" * 16]["score"])  # keeps its old ranking
    assert after["a" * 16]["kind"] == "OTHER" and after["c" * 16]["kind"] == "PROJECT"  # the rest were re-ranked
    version = sqlite3.connect(path).execute("SELECT value FROM meta WHERE key = 'classifier_version'").fetchone()
    assert version[0] == str(CLASSIFIER_VERSION)  # the version is still written, so it is not retried forever


def test_read_only_database_skips_the_rerank_and_still_serves_reads(tmp_path, monkeypatch):
    path = tmp_path / "leads.sqlite3"
    LeadStore(path).start_run("r1", "q", "query text", NOW)  # a normal, current database
    conn = sqlite3.connect(path)
    conn.execute("DELETE FROM meta")  # make the stored classifier version stale
    conn.commit()
    conn.close()
    real_connect = sqlite3.connect
    monkeypatch.setattr(sqlite3, "connect", lambda p, **kw: real_connect(f"file:{Path(p).as_posix()}?mode=ro",
                                                                          uri=True, **kw))
    store = LeadStore(path)
    assert store.runs()[0]["run_id"] == "r1"  # no write was needed to read
    assert store.last_run() is None
    monkeypatch.undo()
    assert sqlite3.connect(path).execute("SELECT COUNT(*) FROM meta").fetchone()[0] == 0  # nothing was written


def test_concurrent_opens_of_an_old_database_are_safe(tmp_path):
    path = tmp_path / "leads.sqlite3"
    make_old_db(path)
    errors = []

    def open_and_list():
        try:
            store = LeadStore(path)
            for _ in range(3):
                store.leads()
        except Exception as exc:  # noqa: BLE001 - the test reports whatever escaped
            errors.append(exc)

    threads = [threading.Thread(target=open_and_list) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert {row["id"]: row["status"] for row in snapshot(path)} == {
        "a" * 16: "DISMISSED", "b" * 16: "CAPTURED", "c" * 16: "SNOOZED", "d" * 16: "NEW"}


def test_catalog_domains_become_official_hosts_and_trigger_a_rerank(tmp_path):
    root = tmp_path / "wb"
    store_path = root / "leads.sqlite3"
    LeadStore(store_path).upsert_hit("https://buyer.example.org/rfp", "Solicitation: power", "", "web", "q", NOW)
    plain = snapshot(store_path)[0]["score"]
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"schema_version": "trailforge-discovery-catalog-v1", "queries": [
        {"id": "q1", "query": "power rfp", "domains": ["buyer.example.org"], "sources": ["web"], "limit": 5}]}),
        encoding="utf-8")
    service = FindService(root)
    service.set_catalog(catalog)
    service.store.counts()
    assert snapshot(store_path)[0]["score"] == plain + 8
    service.set_catalog(None)  # without the catalog the host is an ordinary one again
    service.store.counts()
    assert snapshot(store_path)[0]["score"] == plain


# ----- host spoofing, deadline false positives, recall words, nits -----
@pytest.mark.parametrize("url", ["https://x.gov.attacker.com/a", "https://sam.gov.evil.example/a",
                                 "https://rfp.gov.attacker.com/a", "https://evilpsegliny.com/a",
                                 "https://notlightrfp.com/a", "https://company.us/a", "https://x.gov.uk.evil.com/a"])
def test_lookalike_hosts_are_neither_official_nor_portals(url):
    plain = classify("Solicitation: power", "", "https://x.example/a")
    found = classify("Solicitation: power", "", url)
    assert found.score == plain.score and not any(t.startswith("host:") for t in found.rfp)


@pytest.mark.parametrize("url", ["https://foo.gov.uk/a", "https://city.gov/a", "https://x.mil/a",
                                 "https://www.psegliny.com/a", "https://ci.town.tx.us/a"])
def test_real_official_hosts_count(url):
    plain = classify("Solicitation: power", "", "https://x.example/a")
    assert classify("Solicitation: power", "", url).score == plain.score + 8
    assert classify("Solicitation: power", "", "https://sam.gov/a").rfp[-1] == "host:sam.gov"


@pytest.mark.parametrize("snippet", [
    "Operations were delayed due to the storm on October 5, 2025.",
    "Due to funding, the board met on 2026-03-01.",
    "The firm submitted comments on 2025-03-01.",
    "Submission received 2025-03-01.",
])
def test_ordinary_sentences_are_not_deadline_hints(snippet):
    assert deadline_hint("RFP for power", snippet) is None
    found = classify("Temporary power RFP", snippet, "https://x.example/a")
    assert found.deadline is None and found.score == classify("Temporary power RFP", "", "https://x.example/a").score


def test_deadline_wording_that_is_still_accepted_names_its_word():
    assert deadline_hint("", "Bids must be submitted by October 30, 2026")["word"] == "submitted"
    assert deadline_hint("", "Proposals are due Oct. 30, 2026. Due to funding, extra time.")["word"] == "due"
    assert deadline_hint("", "Submissions by 2026-11-02")["word"] == "submissions"
    assert deadline_hint("", "Submit proposals no later than 11/02/2026")["word"] == "submit"


def test_recall_wording_surfaces_rfp_like_leads():
    for title, snippet, url in [
        ("Request for Information: Temporary Generation", "", "https://utility.example.org/rfi"),
        ("RFI for bridge power", "", "https://x.example/a"),
        ("City soliciting proposals for 200 MW of bridge power", "", "https://blog.example/n"),
        ("Port seeks bids for generator rental", "", "https://x.example/a"),
        ("Sealed bids for diesel generators", "", "https://x.example/a"),
        ("Notice", "Proposals will be opened Monday for the generator replacement", "https://x.example/a"),
        ("Temporary generation procurement update", "", "https://x.example/a"),
        ("Letter", "400 MW of temporary generation", "https://x.example/procurement-office-letter.pdf"),
    ]:
        found = classify(title, snippet, url)
        assert found.kind == "RFP", (title, found.reason)
    # official-host-only words: an addendum or a /bids/ page counts on an official host, nowhere else
    assert classify("Addendum No. 1", "power purchase", "https://www.psegliny.com/x.pdf").kind == "RFP"
    assert classify("Addendum No. 1", "power purchase", "https://blog.example/x.pdf").kind == "OTHER"
    assert classify("Notice", "generator", "https://www.aspower.com/bids/gen.pdf").kind == "RFP"
    assert classify("Notice", "generator", "https://blog.example/bids/gen.pdf").kind == "OTHER"


@pytest.mark.parametrize("title,snippet", [
    ("What is a Request for Information?", "An RFI gathers vendor data."),
    ("What is a Request for Information for power?", "How utilities use an RFI."),
    ("Glossary of Procurement Terms", "RFP, RFQ, RFI and solicitation explained for power buyers"),
    ("RFI template for energy utilities", ""),
    ("Understanding sealed bids for generators", ""),
])
def test_recall_words_do_not_admit_explainers(title, snippet):
    found = classify(title, snippet, "https://blog.example/post")
    assert found.kind == "OTHER" and found.reason.startswith(("explainer-like", "RFP wording but no energy"))


def test_portal_host_without_energy_context_is_a_lower_ranked_flagged_rfp():
    bare = classify("Janitorial services", "Annual contract.", "https://www.bidnetdirect.com/x/123")
    withctx = classify("Janitorial services", "Annual contract for power plant cleaning.",
                       "https://www.bidnetdirect.com/x/123")
    assert bare.kind == withctx.kind == "RFP"
    assert bare.reason == "procurement portal host, but no energy or power context in the snippet"
    assert withctx.reason == "" and bare.score < withctx.score - 10
    assert classify("Janitorial services RFP", "", "https://city.example.com/x").kind == "OTHER"  # words alone: Other


def test_gw_needs_a_number_and_generation_capacity_need_power_words():
    assert "GW" not in classify("GW Law professor", "", "https://law.example.edu/a").power
    assert "GW" not in classify("GW", "the GW campus", "https://x.example/a").power
    for text in ("a 5-GW campus", "7.65 GW gas plant", "2 GW"):
        assert "GW" in classify(text, "", "https://x.example/a").power
    for text in ("RFP", "RFP for capacity building", "RFP for next generation software"):
        assert classify(text, "", "https://x.example/a").kind == "OTHER", text
    for text in ("RFP for power generation", "RFP for 20 MW capacity", "RFP for electric capacity",
                 "RFP for energy generation"):
        assert classify(text, "", "https://x.example/a").kind == "RFP", text


def test_curly_apostrophe_and_project_name_stoplist():
    assert "what is/are" in classify("What’s the difference between RFP types", "", "https://x.example/a").explainer
    named = classify("Plant planned", "Project Jupiter gas plant", "https://x.example/a").score
    generic = classify("Plant planned", "Project Description: gas plant", "https://x.example/a").score
    manager = classify("Plant planned", "Project Manager: gas plant", "https://x.example/a").score
    assert named == generic + 6 == manager + 6


def test_official_hosts_must_be_real_multi_label_hostnames():
    store = LeadStore(Path("unused.sqlite3"), ["org", "COM", " Buyer.Example.org ", "x y.org", "a.org/path", 5, None])
    assert store._official_hosts == ("buyer.example.org",)


def test_service_ignores_odd_catalog_domain_values(tmp_path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"schema_version": "trailforge-discovery-catalog-v1", "queries": [
        {"id": "q1", "query": "power rfp", "domains": ["org", "buyer.example.org"], "sources": ["web"], "limit": 5},
        {"id": "q2", "query": "power rfp two", "sources": ["web"], "limit": 5}]}), encoding="utf-8")
    service = FindService(tmp_path / "wb")
    service.set_catalog(catalog)
    assert service.store._official_hosts == ("buyer.example.org",)


def test_deadline_status_uses_the_local_calendar_day(tmp_path):
    store = LeadStore(tmp_path / "leads.sqlite3")
    lead_id, _ = store.upsert_hit("https://www.lightrfp.com/bid/1", "2026 Temporary Generation RFP",
                                  "Proposals are due by 2026-10-30.", "web", "q", NOW)
    expected = "future" if date(2026, 10, 30) >= NOW.astimezone().date() else "past"
    assert store.get(lead_id, NOW)["deadline_status"] == expected
