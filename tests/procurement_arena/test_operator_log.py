import http.client
import json
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

from athena_procurement_arena import local_ui
from athena_procurement_arena.mining import load_project
from athena_procurement_arena.operator_log import OperatorLog, OperatorLogError

ROOT = Path(__file__).resolve().parents[2]
STIBNITE = ROOT / "scenarios/fixtures/mining/stibnite/project.json"
NOW = datetime(2026, 10, 22, tzinfo=UTC)


@pytest.fixture
def log(tmp_path):
    project = load_project(STIBNITE)
    return OperatorLog(tmp_path / "log.jsonl", {project["project_id"]: project}), project


def _req(project):
    return project["requirements"][0]["requirement_id"]


def test_events_chain_persist_and_detect_tampering(log, tmp_path):
    operator, project = log
    rid = _req(project)
    operator.append(kind="claim_review", project_id="stibnite", requirement_id=rid, reviewer="Nick",
                    payload={"field": "phase", "decision": "REVIEWED"}, now=NOW)
    operator.append(kind="claim_review", project_id="stibnite", requirement_id=rid, reviewer="Nick",
                    payload={"field": "use_case", "decision": "REJECTED", "note": "wrong"}, now=NOW)
    assert OperatorLog(tmp_path / "log.jsonl", {"stibnite": project}).view()["head"] == operator.view()["head"]
    text = (tmp_path / "log.jsonl").read_text().replace("REVIEWED", "REJECTED")
    (tmp_path / "log.jsonl").write_text(text)
    with pytest.raises(OperatorLogError, match="tampered"):
        OperatorLog(tmp_path / "log.jsonl", {"stibnite": project})


def test_reviewer_name_and_known_targets_required(log):
    operator, project = log
    rid = _req(project)
    ok = {"field": "phase", "decision": "REVIEWED"}
    for bad in (dict(reviewer=" ", project_id="stibnite", requirement_id=rid, payload=ok),
                dict(reviewer="N", project_id="nope", requirement_id=rid, payload=ok),
                dict(reviewer="N", project_id="stibnite", requirement_id="nope", payload=ok),
                dict(reviewer="N", project_id="stibnite", requirement_id=rid, payload={**ok, "field": "demand.nope"})):
        with pytest.raises(OperatorLogError):
            operator.append(kind="claim_review", **bad)
    assert operator.events == []


def test_correction_supersedes_without_rewriting_history(log):
    operator, project = log
    rid = _req(project)
    first = operator.append(kind="claim_review", project_id="stibnite", requirement_id=rid, reviewer="N",
                            payload={"field": "phase", "decision": "REVIEWED"}, now=NOW)
    second = operator.append(kind="claim_review", project_id="stibnite", requirement_id=rid, reviewer="N",
                             payload={"field": "phase", "decision": "REJECTED"}, supersedes=first["event_id"], now=NOW)
    with pytest.raises(OperatorLogError, match="already superseded"):
        operator.append(kind="claim_review", project_id="stibnite", requirement_id=rid, reviewer="N",
                        payload={"field": "phase", "decision": "REVIEWED"}, supersedes=first["event_id"], now=NOW)
    reviews = operator.view()["projects"]["stibnite"]["claim_review"]
    assert [e["superseded"] for e in reviews] == [True, False] and second["supersedes"] == 1


def test_activity_rejects_future_and_naive_times_and_needs_outcome(log):
    operator, project = log
    rid = _req(project)
    base = dict(kind="activity", project_id="stibnite", requirement_id=rid, reviewer="N", now=NOW)
    for payload in ({"entry": "CONVERSATION", "occurred_at": "2027-01-01T00:00:00+00:00", "summary": "x"},
                    {"entry": "CONVERSATION", "occurred_at": "2026-10-01T00:00:00", "summary": "x"},
                    {"entry": "OUTCOME", "occurred_at": "2026-10-01T00:00:00+00:00", "summary": "x"}):
        with pytest.raises(OperatorLogError):
            operator.append(payload=payload, **base)
    event = operator.append(payload={"entry": "OUTCOME", "outcome": "QUALIFIED", "summary": "call held",
                                     "occurred_at": "2026-10-01T00:00:00+00:00"}, **base)
    assert event["payload"]["outcome"] == "QUALIFIED"


def test_fuel_providers_gated_behind_direct_buyer_and_conversation(log):
    operator, project = log
    rid = _req(project)
    source = next(iter(project["sources"]))
    chain = lambda role: operator.append(  # noqa: E731
        kind="buying_chain", project_id="stibnite", reviewer="N", now=NOW,
        payload={"organization": "Org", "role": role, "evidence_quote": "q", "evidence_source": source})
    with pytest.raises(OperatorLogError, match="fuel gate"):
        chain("FUEL_PROVIDER")
    chain("EPCM")
    with pytest.raises(OperatorLogError, match="fuel gate"):
        chain("FUEL_PROVIDER")
    operator.append(kind="activity", project_id="stibnite", requirement_id=rid, reviewer="N", now=NOW,
                    payload={"entry": "CONVERSATION", "summary": "intro", "occurred_at": "2026-10-01T00:00:00+00:00"})
    assert chain("FUEL_PROVIDER")["payload"]["role"] == "FUEL_PROVIDER"
    with pytest.raises(OperatorLogError, match="evidence_source"):
        operator.append(kind="buying_chain", project_id="stibnite", reviewer="N", now=NOW,
                        payload={"organization": "Org", "role": "EPC", "evidence_quote": "q", "evidence_source": "zzz"})


def test_source_note_hashes_excerpt_and_stamps_first_observed(log):
    operator, _ = log
    event = operator.append(kind="source_note", project_id="stibnite", reviewer="N", now=NOW, payload={
        "url": "https://example.com/a", "title": "T", "excerpt": "hello", "access": "CONFIDENTIAL"})
    assert event["payload"]["excerpt_sha256"] == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert event["recorded_at"] == NOW.isoformat()
    with pytest.raises(OperatorLogError, match="http"):
        operator.append(kind="source_note", project_id="stibnite", reviewer="N", payload={
            "url": "file:///etc/passwd", "title": "T", "excerpt": "x", "access": "PUBLIC"})


def test_http_endpoint_requires_token_and_persists(tmp_path):
    app = local_ui.Workbench(tmp_path, [], [STIBNITE])
    server = local_ui.WorkbenchServer(app, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        def call(method, body=None, token=None):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            headers = {"Host": server.authority}
            data = None
            if body is not None:
                data = json.dumps(body)
                headers |= {"Content-Type": "application/json", "Content-Length": str(len(data))}
            if token:
                headers["X-Trailforge-Token"] = token
            conn.request(method, "/api/operator", body=data, headers=headers)
            response = conn.getresponse()
            return response.status, json.loads(response.read())
        rid = app.mining[0]["requirements"][0]["requirement_id"]
        body = {"kind": "claim_review", "project_id": "stibnite", "requirement_id": rid, "reviewer": "Nick",
                "payload": {"field": "phase", "decision": "REVIEWED"}}
        assert call("POST", body)[0] == 403
        assert call("POST", {**body, "extra": 1}, app.token)[0] == 400
        assert call("POST", body, app.token)[0] == 201
        status, view = call("GET")
        assert status == 200 and view["events"] == 1
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        app.close()
