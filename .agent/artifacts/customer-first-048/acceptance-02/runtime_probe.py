"""Controller process/restart proof; never sends external messages."""
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[4]
USE_INSTALLED = "--installed" in sys.argv
def request(origin, method, path, data=None, token=None, raw=None, extra=None):
    address = urlsplit(origin)
    conn = http.client.HTTPConnection(address.hostname, address.port, timeout=10)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Operator-Token"] = token
    headers.update(extra or {})
    body = raw if raw is not None else (json.dumps(data) if data is not None else None)
    conn.request(method, path, body=body, headers=headers)
    reply = conn.getresponse()
    result = (reply.status, json.loads(reply.read()))
    conn.close()
    return result

def start(db):
    env = dict(os.environ)
    if USE_INSTALLED:
        env.pop("PYTHONPATH", None)
    else:
        env["PYTHONPATH"] = str(ROOT / "src")
    proc = subprocess.Popen([sys.executable, "-m", "athena_procurement_arena.operator",
                             "--data", str(db), "--port", "0"],
                            cwd=db.parent if USE_INSTALLED else ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    line = proc.stdout.readline()
    if "http://127.0.0.1:" not in line:
        proc.terminate()
        raise RuntimeError("operator startup failed: " + line + proc.stderr.read())
    origin = line[line.index("http://"):].split()[0].rstrip("/")
    return proc, origin

def stop(proc):
    proc.terminate()
    proc.wait(timeout=10)

def evidence(claim, value):
    text = "Synthetic acceptance evidence: " + claim + " = " + value
    return {"id": os.urandom(16).hex(), "claim": claim, "value": value,
            "source_url": "https://example.com/synthetic-test", "excerpt": text,
            "source_date": "2026-10-01", "observed_at": datetime.now(timezone.utc).isoformat(),
            "reviewer": "SYNTHETIC TEST ONLY", "review_status": "REVIEWED",
            "sha256": hashlib.sha256(text.encode()).hexdigest(), "supersedes": []}

def save(origin, token, doc):
    doc = {k: v for k, v in doc.items() if k not in {"gate", "_history_lengths"}}
    doc["version"] += 1
    code, result = request(origin, "POST", "/api/projects/" + doc["id"], doc, token)
    assert code == 201, (code, result)
    return result

def main():
    checks = []
    # Windows may briefly retain terminated-child file handles. Cleanup is not
    # an application assertion; leave that private temporary folder if locked.
    with tempfile.TemporaryDirectory(prefix="trailforge-controller-", ignore_cleanup_errors=True) as folder:
        db = Path(folder) / "acceptance.sqlite3"
        proc, origin = start(db)
        try:
            address = urlsplit(origin)
            for resource, marker in (("/", b"Trailforge"), ("/app.js", b""), ("/style.css", b"")):
                connection = http.client.HTTPConnection(address.hostname, address.port, timeout=10)
                connection.request("GET", resource)
                response = connection.getresponse()
                content = response.read()
                assert response.status == 200 and content and marker.lower() in content.lower(), resource
                connection.close()
            checks.append("HTML, JavaScript and stylesheet served from package")
            _, session = request(origin, "GET", "/api/session")
            token = session["token"]
            code, doc = request(origin, "POST", "/api/projects", {
                "name": "SYNTHETIC acceptance project", "location": "TEST ONLY", "phase": "Early signal"}, token)
            assert code == 201, (code, doc)
            assert not doc["gate"]["fuel_unlocked"]
            checks.append("early intake without RFP, known MW or fuel")
            bad = json.loads(json.dumps(doc))
            bad["version"] += 1
            bad["fuel"]["notes"] = "SYNTHETIC premature supplier coordination"
            code, _ = request(origin, "POST", "/api/projects/" + doc["id"], bad, token)
            assert code == 400, code
            checks.append("new fuel notes rejected while customer gate is locked")
            bad = json.loads(json.dumps(doc))
            bad["version"] += 1
            proof = evidence("scope", "bridge")
            proof["source_url"] = ""
            bad["evidence"].append(proof)
            code, _ = request(origin, "POST", "/api/projects/" + doc["id"], bad, token)
            assert code == 400, code
            checks.append("reviewed power scope without traceable source rejected")
            code, _ = request(origin, "POST", "/api/projects", {}, raw='{"name":"a","name":"b"}', token=token)
            assert code == 400, code
            code, _ = request(origin, "POST", "/api/projects", {"name": "Unauthorized"})
            assert code == 403, code
            code, _ = request(origin, "GET", "/api/session", extra={"Origin": "https://example.com"})
            assert code == 403, code
            checks.append("duplicate JSON keys, missing token and cross-origin request rejected")
            doc["evidence"] = [evidence("project", "Synthetic project"), evidence("scope", "bridge")]
            doc = save(origin, token, doc)
            assert doc["gate"]["need"] == "VERIFIED"
            assert doc["gate"]["buyer"] == "UNKNOWN"
            assert not doc["gate"]["fuel_unlocked"]
            checks.append("evidenced need can precede MW/buyer; fuel remains locked")
            stale = dict(doc)
            doc["brief"] = "TEST ONLY: Who owns commissioning power and what remains unserved?"
            doc = save(origin, token, doc)
            stale["version"] += 1
            code, _ = request(origin, "POST", "/api/projects/" + doc["id"], stale, token)
            assert code == 409, code
            checks.append("stale edit rejected")
            buyer = evidence("buyer", "Synthetic Buyer owns project power procurement")
            doc["evidence"].append(buyer)
            doc["people"].append({"name": "Synthetic Buyer", "organization": "TEST CUSTOMER",
                                  "role": "BUYER", "source_evidence": buyer["id"],
                                  "contact_route": "TEST ONLY — no real address"})
            doc = save(origin, token, doc)
            assert doc["gate"]["buyer"] == "KNOWN" and not doc["gate"]["fuel_unlocked"]
            premature = {k: v for k, v in doc.items() if k not in {"gate", "_history_lengths"}}
            premature = json.loads(json.dumps(premature))
            premature["version"] += 1
            premature["fuel"]["status"] = "PLANNING"
            code, _ = request(origin, "POST", "/api/projects/" + doc["id"], premature, token)
            assert code == 400, code
            checks.append("server rejects fuel planning before conversation")
            doc["interactions"].append({"occurred_at": datetime.now(timezone.utc).isoformat(),
                "person": "Synthetic Buyer", "notes": "SYNTHETIC TEST ONLY: customer requirements confirmed",
                "needs_understood": True, "learned_mw": "2", "timing": "2027-02-01",
                "duration": "6 months", "site_constraints": "SYNTHETIC permitted pad; delivery access confirmed"})
            doc = save(origin, token, doc)
            assert doc["gate"]["fuel_unlocked"]
            doc["fuel"] = {"status": "PLANNING", "notes": "SYNTHETIC downstream fuel planning only"}
            doc = save(origin, token, doc)
            checks.append("source-backed test buyer + understood test conversation unlocks downstream fuel")
            code, exported = request(origin, "GET", "/api/projects/" + doc["id"] + "/export")
            assert code == 200 and exported["interactions"] == doc["interactions"]
            checks.append("dossier export includes retained conversation and source evidence")
            project_id = doc["id"]
        finally:
            stop(proc)
        proc, origin = start(db)
        try:
            code, retained = request(origin, "GET", "/api/projects/" + project_id)
            assert code == 200 and retained["brief"] == doc["brief"]
            assert retained["evidence"] == doc["evidence"]
            assert retained["fuel"] == doc["fuel"] and retained["gate"]["fuel_unlocked"]
            checks.append("separate-process restart retains evidence and brief")
            _, session = request(origin, "GET", "/api/session")
            denied = evidence("scope", "Need cancelled")
            denied["review_status"] = "CONTRADICTED"
            retained["evidence"].append(denied)
            retained["fuel"]["status"] = "NOT_STARTED"
            retained = save(origin, session["token"], retained)
            assert not retained["gate"]["fuel_unlocked"]
            assert retained["fuel"]["notes"] == "SYNTHETIC downstream fuel planning only"
            bad = json.loads(json.dumps(retained))
            bad["version"] += 1
            bad["fuel"]["notes"] = "SYNTHETIC changed coordination while relocked"
            code, _ = request(origin, "POST", "/api/projects/" + retained["id"], bad, session["token"])
            assert code == 400, code
            checks.append("lawful notes preserved on relock; changed fuel notes rejected")
            checks.append("contradicted need relocks downstream fuel without deleting history")
            restored = evidence("scope", "bridge")
            restored["supersedes"] = [denied["id"]]
            retained["evidence"].append(restored)
            retained = save(origin, session["token"], retained)
            assert retained["gate"]["fuel_unlocked"]
            checks.append("explicit correction resolves contradiction and preserves source history")
        finally:
            stop(proc)
        with sqlite3.connect(db) as connection:
            connection.execute("UPDATE projects SET payload=? WHERE id=?", ('{"broken":true}', project_id))
        connection.close()
        proc, origin = start(db)
        try:
            code, listing = request(origin, "GET", "/api/projects")
            assert code == 200 and listing["projects"][0]["integrity"] == "FAIL"
            code, _ = request(origin, "GET", "/api/projects/" + project_id)
            assert code == 404
            checks.append("corrupt dossier remains visible as unreadable and cannot be treated as qualified")
        finally:
            stop(proc)
    print(json.dumps({"status": "PASS", "checks": checks,
                      "installed_wheel": USE_INSTALLED,
                      "real_conversations": False, "finished_utc": datetime.now(timezone.utc).isoformat()}, indent=2))

if __name__ == "__main__":
    main()
