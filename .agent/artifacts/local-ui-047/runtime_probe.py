"""Controller process-restart/package proof against the public loopback API."""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import queue
import shutil
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from urllib.parse import urlsplit


def start(root, bundle=None):
    command = [sys.executable, "-m", "athena_procurement_arena.local_ui",
               "--experiments-dir", str(root), "--port", "0"]
    command += ["--bundle", str(bundle)] if bundle else ["--saved-only"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    lines = queue.Queue()
    threading.Thread(target=lambda: lines.put(process.stdout.readline()), daemon=True).start()
    try:
        line = lines.get(timeout=30)
        assert "Trailforge workbench: http://127.0.0.1:" in line, line
        origin = line.split("Trailforge workbench: ", 1)[1].split("/ (", 1)[0]
        return process, origin
    except BaseException:
        stop(process)
        raise


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def request(origin, path, payload=None, token=None, headers=None):
    target = urlsplit(origin)
    connection = http.client.HTTPConnection(target.hostname, target.port, timeout=15)
    body = None if payload is None else json.dumps(payload)
    extra = {} if headers is None else dict(headers)
    if body is not None:
        extra.setdefault("Content-Type", "application/json")
        extra.setdefault("Origin", origin)
    if token is not None:
        extra["X-Trailforge-Token"] = token
    connection.request("GET" if payload is None else "POST", path, body=body, headers=extra)
    response = connection.getresponse()
    data = response.read()
    status = response.status
    kind = response.getheader("Content-Type", "")
    connection.close()
    return status, json.loads(data) if "application/json" in kind else data


def hashes(path):
    return {item.name: hashlib.sha256(item.read_bytes()).hexdigest()
            for item in path.glob("*.json")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence_root.resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    root = evidence / "runs"
    bundle = evidence / "bundle.json"
    shutil.copyfile(args.bundle, bundle)
    process, origin = start(root, bundle)
    checks = []
    try:
        for asset in ("/", "/app.js", "/style.css"):
            status, data = request(origin, asset)
            assert status == 200 and len(data) > 100, asset
        checks.append("packaged-static-assets")
        status, session = request(origin, "/api/session")
        assert status == 200 and session["cases"][0]["fixture"]["fixture_id"] == "GT-003"
        token, case = session["token"], session["cases"][0]["id"]
        status, first = request(origin, "/api/run", {"case_id": case}, token)
        assert status == 201 and first["integrity"] == "PASS", first
        run_id = first["id"]
        assert first["replay"]["status"] == "NOT_RUN"
        assert first["evaluation"]["status"] == "UNSEALED"
        assert first["evaluation"]["scoring"] == "UNSCORED"
        assert first["input"]["fixture_context"]["fixture"]["verified_by"]
        before = hashes(root / run_id)
        status, replay = request(origin, "/api/replay", {"run_id": run_id}, token)
        assert status == 200 and replay["replay"]["status"] == "PASS", replay
        assert all(replay["replay"]["checks"].values())
        assert hashes(root / run_id) == before
        checks.append("real-save-inspect-replay-no-artifact-mutation")
        status, second = request(origin, "/api/run", {"case_id": case}, token)
        assert status == 201 and second["id"] != run_id
        assert first["decisions"] == second["decisions"]
        checks.append("deterministic-repeat-separate-run")
        assert request(origin, "/api/run", {"case_id": case})[0] == 403
        assert request(origin, "/api/run", {"case_id": case}, token,
                       {"Origin": "http://foreign.invalid"})[0] == 403
        assert request(origin, "/api/session", headers={"Host": "foreign.invalid"})[0] == 403
        assert request(origin, "/api/run")[0] >= 400
        assert request(origin, "/api/runs/../input.json")[0] >= 400
        checks.append("http-boundary-refusals")
    finally:
        stop(process)
    bundle.rename(evidence / "original-source-unavailable.json")
    process, origin = start(root)
    try:
        status, session = request(origin, "/api/session")
        assert status == 200 and session["cases"] == []
        token = session["token"]
        status, reopened = request(origin, f"/api/runs/{run_id}")
        assert status == 200 and reopened["integrity"] == "PASS"
        assert reopened["replay"]["status"] == "NOT_RUN"
        status, replay = request(origin, "/api/replay", {"run_id": run_id}, token)
        assert status == 200 and replay["replay"]["status"] == "PASS", replay
        assert hashes(root / run_id) == before
        checks.append("fresh-process-source-unavailable-replay")
        corrupt_id = uuid.uuid4().hex
        corrupt = root / corrupt_id
        shutil.copytree(root / run_id, corrupt)
        with (corrupt / "input.json").open("ab") as stream:
            stream.write(b" ")
        bad_hashes = hashes(corrupt)
        status, result = request(origin, f"/api/runs/{corrupt_id}")
        assert status == 422 and result["integrity"] == "FAIL", result
        status, result = request(origin, "/api/replay", {"run_id": corrupt_id}, token)
        assert status == 422 and result["integrity"] == "FAIL", result
        assert hashes(corrupt) == bad_hashes
        status, listing = request(origin, "/api/runs")
        assert status == 200 and any(item["id"] == corrupt_id and item["integrity"] == "FAIL"
                                     for item in listing["runs"])
        checks.append("corruption-visible-and-not-healed")
    finally:
        stop(process)
    print(json.dumps({"status": "PASS", "checks": checks, "evidence_root": str(evidence),
                      "run_id": run_id, "artifact_hashes": before}, indent=2))


if __name__ == "__main__":
    main()
