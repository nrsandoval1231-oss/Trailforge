import hashlib
import http.client
import json
import threading

import pytest

from athena_procurement_arena.operator import Server, Store, blank, gate


def evidence(
    claim, value, status="REVIEWED", excerpt="Source states this fact.", reviewer="Reviewer", source_url="https://example.test/project"
):
    import secrets

    return {
        "id": secrets.token_hex(16),
        "claim": claim,
        "value": value,
        "source_url": source_url,
        "excerpt": excerpt,
        "source_date": "2026-09-01",
        "observed_at": "2026-10-01T12:00:00Z",
        "reviewer": reviewer if status == "REVIEWED" else "",
        "review_status": status,
        "sha256": hashlib.sha256(excerpt.encode()).hexdigest(),
        "supersedes": [],
    }


def valid_need(doc):
    doc["evidence"].append(evidence("scope", "temporary power"))
    return doc


def test_early_project_and_unknown_quantity_are_usable(tmp_path):
    store = Store(tmp_path / "desk.sqlite3")
    p = store.save(blank("CLOP facility", "Ohio", "Permitting"))
    assert p["gate"]["need"] == "UNKNOWN"
    p.pop("gate")
    p.pop("_history_lengths")
    p["evidence"].append(evidence("scope", "temporary power"))
    p["evidence"].append(evidence("required_mw", "UNKNOWN", status="UNKNOWN", excerpt=""))
    p["version"] += 1
    saved = store.save(p)
    assert saved["gate"]["need"] == "VERIFIED"
    assert saved["gate"]["claims"]["required_mw"] == "UNKNOWN"
    store.close()


@pytest.mark.parametrize("scope", ["no temporary need", "non-temporary", "unknown", "bridge power outage canceled"])
def test_scope_requires_explicit_allowed_value(tmp_path, scope):
    p = blank("Project", "", "")
    p["evidence"].append(evidence("scope", scope))
    assert gate(p)["need"] == "UNKNOWN"


@pytest.mark.parametrize("claim", ["scope", "buyer"])
def test_reviewed_scope_and_buyer_require_traceable_source_on_write(tmp_path, claim):
    store = Store(tmp_path / f"{claim}.sqlite3")
    doc = blank("Project", "", "")
    doc["evidence"].append(evidence(claim, "temporary power" if claim == "scope" else "Buyer A", source_url=""))
    with pytest.raises(ValueError, match="traceable HTTP or HTTPS"):
        store.save(doc)
    store.close()


def test_gate_does_not_promote_reviewed_scope_or_buyer_without_source():
    doc = blank("Project", "", "")
    scope = evidence("scope", "temporary power", source_url="")
    buyer = evidence("buyer", "Buyer A", source_url="")
    doc["evidence"].extend([scope, buyer])
    doc["people"].append(
        {"name": "Buyer A", "organization": "Developer", "role": "BUYER", "source_evidence": buyer["id"], "contact_route": ""}
    )
    assert gate(doc)["need"] == "UNKNOWN"
    assert gate(doc)["buyer"] == "UNKNOWN"
    sourced_scope = evidence("scope", "temporary power")
    doc["evidence"].append(sourced_scope)
    assert gate(doc)["need"] == "UNKNOWN"


def test_conflict_or_contradiction_demotes_need_and_relocks_fuel():
    p = blank("Project", "", "")
    valid_need(p)
    buyer_proof = evidence("buyer", "Buyer A", excerpt="Buyer role verified.")
    p["evidence"].append(buyer_proof)
    p["people"].append(
        {
            "name": "Buyer A",
            "organization": "Developer",
            "role": "BUYER",
            "source_evidence": buyer_proof["id"],
            "contact_route": "",
        }
    )
    p["interactions"].append(
        {
            "occurred_at": "2026-10-01T12:00:00Z",
            "person": "Buyer A",
            "notes": "Call",
            "needs_understood": True,
            "learned_mw": "2",
            "timing": "Q2",
            "duration": "6 months",
            "site_constraints": "gas line",
        }
    )
    assert gate(p)["fuel_unlocked"]
    p["evidence"].append(evidence("scope", "permanent capacity"))
    assert gate(p)["need"] == "UNKNOWN"
    assert not gate(p)["fuel_unlocked"]


def test_owner_or_developer_role_does_not_prove_buyer():
    p = blank("Project", "", "")
    p["organizations"].append({"name": "Developer", "role": "DEVELOPER", "source_evidence": ""})
    assert gate(p)["buyer"] == "UNKNOWN"
    p["people"].append(
        {"name": "Person", "organization": "Developer", "role": "BUYER", "source_evidence": "", "contact_route": ""}
    )
    assert gate(p)["buyer"] == "UNKNOWN"
    b = evidence("buyer", "Budget buyer", excerpt="Buyer listed")
    p["evidence"].append(b)
    p["people"][-1]["source_evidence"] = b["id"]
    assert gate(p)["buyer"] == "KNOWN"


def test_correction_supersedes_old_claim_without_erasing_history():
    p = blank("Project", "", "")
    old = evidence("scope", "permanent capacity")
    newer = evidence("scope", "bridge power", excerpt="Correction states bridge power.")
    newer["supersedes"] = [old["id"]]
    p["evidence"] = [old, newer]
    assert gate(p)["need"] == "VERIFIED"
    assert len(p["evidence"]) == 2


def test_buyer_correction_relocks_fuel():
    p = blank("Project", "", "")
    valid_need(p)
    buyer_proof = evidence("buyer", "Buyer A", excerpt="Buyer role verified.")
    p["evidence"].append(buyer_proof)
    p["people"].append(
        {
            "name": "Buyer A",
            "organization": "Org",
            "role": "BUYER",
            "source_evidence": buyer_proof["id"],
            "contact_route": "public switchboard",
        }
    )
    p["interactions"].append(
        {
            "occurred_at": "2026-10-01T12:00:00Z",
            "person": "Buyer A",
            "notes": "Needs learned",
            "needs_understood": True,
            "learned_mw": "2",
            "timing": "Q2",
            "duration": "6 months",
            "site_constraints": "gas",
        }
    )
    assert gate(p)["fuel_unlocked"]
    correction = evidence("buyer", "", status="CONTRADICTED", excerpt="Role assignment disproved.", reviewer="")
    correction["supersedes"] = [buyer_proof["id"]]
    p["evidence"].append(correction)
    assert gate(p)["buyer"] == "UNKNOWN"
    assert not gate(p)["fuel_unlocked"]


def test_fuel_requires_real_person_and_complete_understood_conversation():
    p = blank("Project", "", "")
    valid_need(p)
    p["interactions"].append(
        {
            "occurred_at": "2026-10-01T12:00:00Z",
            "person": "Unknown person",
            "notes": "",
            "needs_understood": True,
            "learned_mw": "2",
            "timing": "Q2",
            "duration": "6 months",
            "site_constraints": "gas",
        }
    )
    assert not gate(p)["fuel_unlocked"]
    p["people"].append(
        {"name": "Contact", "organization": "Org", "role": "EPC", "source_evidence": "", "contact_route": ""}
    )
    p["interactions"][0]["person"] = "Contact"
    p["interactions"][0]["learned_mw"] = "UNKNOWN"
    assert not gate(p)["fuel_unlocked"]


def test_restart_append_only_and_stale_version(tmp_path):
    path = tmp_path / "desk.sqlite3"
    store = Store(path)
    p = store.save(valid_need(blank("Project", "", "")))
    store.close()
    store = Store(path)
    got = store.get(p["id"])
    got.pop("gate")
    got.pop("_history_lengths")
    old = dict(got["evidence"][0])
    got["evidence"][0]["value"] = "changed"
    got["version"] += 1
    with pytest.raises(ValueError, match="excerpt hash|append-only"):
        store.save(got)
    got["evidence"][0] = old
    stale = dict(got)
    stale["version"] = 1
    saved = store.save(got)
    with pytest.raises(ValueError, match="STALE_VERSION"):
        store.save(stale)
    assert saved["gate"]["need"] == "VERIFIED"
    store.close()


def test_store_rejects_fuel_work_before_gate_and_fake_conversation(tmp_path):
    store = Store(tmp_path / "fuel.sqlite3")
    p = blank("Project", "", "")
    p["fuel"]["status"] = "PLANNING"
    with pytest.raises(ValueError, match="fuel coordination is locked"):
        store.save(p)
    p["fuel"]["status"] = "NOT_STARTED"
    p["interactions"].append(
        {
            "occurred_at": "banana",
            "person": "P",
            "notes": "",
            "needs_understood": True,
            "learned_mw": "2",
            "timing": "Q2",
            "duration": "6m",
            "site_constraints": "gas",
        }
    )
    with pytest.raises(ValueError, match="ISO timestamp"):
        store.save(p)
    p["interactions"][0]["occurred_at"] = "2026-10-01T12:00:00Z"
    p["interactions"][0]["learned_mw"] = "banana"
    with pytest.raises(ValueError, match="numeric MW"):
        store.save(p)
    store.close()


def test_future_conversation_cannot_unlock_gate(tmp_path):
    store = Store(tmp_path / "future.sqlite3")
    doc = blank("Project", "", "")
    doc["interactions"].append(
        {
            "occurred_at": "2099-01-01T00:00:00Z",
            "person": "Buyer",
            "notes": "Future event",
            "needs_understood": False,
            "learned_mw": "",
            "timing": "",
            "duration": "",
            "site_constraints": "",
        }
    )
    with pytest.raises(ValueError, match="cannot be in the future"):
        store.save(doc)
    store.close()


def unlocked_customer_doc():
    doc = blank("Project", "Nevada", "Construction")
    scope = evidence("scope", "temporary power")
    buyer = evidence("buyer", "Buyer A", excerpt="Buyer is responsible for project purchasing.")
    doc["evidence"].extend([scope, buyer])
    doc["people"].append(
        {"name": "Buyer A", "organization": "Developer", "role": "BUYER", "source_evidence": buyer["id"], "contact_route": ""}
    )
    doc["interactions"].append(
        {
            "occurred_at": "2026-10-01T12:00:00Z",
            "person": "Buyer A",
            "notes": "Actual conversation",
            "needs_understood": True,
            "learned_mw": "2",
            "timing": "Q2",
            "duration": "6 months",
            "site_constraints": "Nevada site",
        }
    )
    return doc


def test_locked_fuel_notes_rejected_and_lawful_notes_retained_on_relock(tmp_path):
    store = Store(tmp_path / "fuel-lock.sqlite3")
    early = blank("Early project", "", "")
    early["fuel"]["notes"] = "Call supplier before conversation"
    with pytest.raises(ValueError, match="new or changed fuel notes are locked"):
        store.save(early)

    lawful = unlocked_customer_doc()
    lawful["fuel"] = {"status": "COORDINATING", "notes": "Previously authorized coordination context"}
    saved = store.save(lawful)
    assert saved["gate"]["fuel_unlocked"]
    saved.pop("gate")
    saved.pop("_history_lengths")
    contradiction = evidence("scope", "", status="CONTRADICTED", excerpt="Need contradicted", reviewer="")
    contradiction["supersedes"] = [saved["evidence"][0]["id"]]
    saved["evidence"].append(contradiction)
    saved["fuel"]["status"] = "NOT_STARTED"
    saved["version"] += 1
    relocked = store.save(saved)
    assert not relocked["gate"]["fuel_unlocked"]
    assert relocked["fuel"]["notes"] == "Previously authorized coordination context"

    relocked.pop("gate")
    relocked.pop("_history_lengths")
    relocked["brief"] = "Continue customer preparation after the correction"
    relocked["version"] += 1
    later_brief = store.save(relocked)
    assert not later_brief["gate"]["fuel_unlocked"]
    assert later_brief["fuel"]["notes"] == "Previously authorized coordination context"

    later_brief.pop("gate")
    later_brief.pop("_history_lengths")
    later_brief["summary"] = "Continue project work while buyer evidence is unknown"
    later_brief["version"] += 1
    later_summary = store.save(later_brief)
    assert not later_summary["gate"]["fuel_unlocked"]
    assert later_summary["fuel"]["notes"] == "Previously authorized coordination context"

    later_summary.pop("gate")
    later_summary.pop("_history_lengths")
    later_summary["fuel"]["notes"] = "New locked note"
    later_summary["version"] += 1
    with pytest.raises(ValueError, match="new or changed fuel notes are locked"):
        store.save(later_summary)
    store.close()


@pytest.fixture
def running(tmp_path):
    store = Store(tmp_path / "operator.sqlite3")
    server = Server(store, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    store.close()
    thread.join(timeout=2)


def request(server, method, path, payload=None, token=None, host=None):
    conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    data = None if payload is None else json.dumps(payload)
    headers = {"Host": host or server.authority}
    if data is not None:
        headers.update({"Content-Type": "application/json", "Content-Length": str(len(data.encode()))})
    if token is not None:
        headers["X-Operator-Token"] = token
    conn.request(method, path, body=data, headers=headers)
    response = conn.getresponse()
    body = response.read()
    conn.close()
    return response.status, body, response.getheader("Content-Type")


def test_http_create_export_security_and_duplicate_json(running):
    s = running
    status, raw, _ = request(s, "GET", "/api/session")
    token = json.loads(raw)["token"]
    assert status == 200
    assert (
        request(s, "POST", "/api/projects", {"name": "Project", "location": "Ohio", "phase": "Early"}, token=token)[0]
        == 201
    )
    assert (
        request(s, "POST", "/api/projects", {"name": "Project", "location": "Ohio", "phase": "Early"}, token=token)[0]
        == 400
    )
    assert request(s, "GET", "/api/projects", host="evil.test")[0] == 403
    assert request(s, "POST", "/api/projects", {"name": "bad", "location": "", "phase": ""})[0] == 403
    conn = http.client.HTTPConnection("127.0.0.1", s.server_port, timeout=3)
    raw = b'{"name":"A","name":"B","location":"","phase":""}'
    conn.request(
        "POST",
        "/api/projects",
        body=raw,
        headers={
            "Host": s.authority,
            "Content-Type": "application/json",
            "Content-Length": str(len(raw)),
            "X-Operator-Token": token,
        },
    )
    assert conn.getresponse().status == 400
    conn.close()
    project = s.store.listing()[0]
    status, body, kind = request(s, "GET", f"/api/projects/{project['id']}/export")
    assert status == 200 and kind.startswith("application/json") and json.loads(body)["name"] == "Project"


def test_update_requires_url_id_and_immutable_history(running):
    s = running
    token = s.token
    created = json.loads(request(s, "POST", "/api/projects", {"name": "P", "location": "", "phase": ""}, token)[1])
    doc = {k: v for k, v in created.items() if k not in {"gate", "_history_lengths"}}
    doc["version"] += 1
    assert request(s, "POST", "/api/projects/" + "0" * 32, doc, token)[0] == 400
    doc["id"] = created["id"]
    doc["evidence"].append(evidence("scope", "temporary"))
    assert request(s, "POST", f"/api/projects/{doc['id']}", doc, token)[0] == 201
    changed = json.loads(request(s, "GET", f"/api/projects/{doc['id']}")[1])
    changed["evidence"][0]["value"] = "mutated"
    changed["version"] += 1
    assert request(s, "POST", f"/api/projects/{doc['id']}", changed, token)[0] == 400


def test_http_returns_authoritative_relocked_gate_for_unknown_buyer(running):
    s = running
    saved = s.store.save(unlocked_customer_doc())
    assert saved["gate"]["fuel_unlocked"]
    doc = {k: v for k, v in saved.items() if k not in {"gate", "_history_lengths"}}
    doc["evidence"].append(evidence("buyer", "UNKNOWN", status="UNKNOWN", excerpt="", reviewer="", source_url=""))
    doc["fuel"]["status"] = "NOT_STARTED"
    doc["version"] += 1
    status, body, _ = request(s, "POST", f"/api/projects/{doc['id']}", doc, s.token)
    assert status == 201
    returned = json.loads(body)
    assert returned["gate"]["buyer"] == "UNKNOWN"
    assert returned["gate"]["fuel_unlocked"] is False
    assert returned["fuel"]["notes"] == saved["fuel"]["notes"]


def test_future_dated_evidence_is_rejected_on_write(tmp_path):
    store = Store(tmp_path / "future.sqlite3")
    doc = blank("Project", "", "")
    future = evidence("scope", "temporary power")
    future["observed_at"] = "2099-01-01T00:00:00Z"
    doc["evidence"].append(future)
    with pytest.raises(ValueError, match="cannot be in the future"):
        store.save(doc)
    store.close()


def test_grown_dossier_still_saves_over_http(running):
    s = running
    created = json.loads(request(s, "POST", "/api/projects", {"name": "Big", "location": "", "phase": ""}, s.token)[1])
    doc = {k: v for k, v in created.items() if k not in {"gate", "_history_lengths"}}
    for i in range(12):  # well past the old 64 KiB request limit
        doc["evidence"].append(evidence("project", f"fact {i}", excerpt=("x" * 11990) + f"{i:010d}"))
    doc["version"] += 1
    status, body, _ = request(s, "POST", f"/api/projects/{doc['id']}", doc, s.token)
    assert status == 201, body
