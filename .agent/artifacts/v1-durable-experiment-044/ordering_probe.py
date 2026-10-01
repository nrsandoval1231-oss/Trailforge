"""Acceptance probe: valid input order need not equal sorted ledger ID order."""
import json
import tempfile
from pathlib import Path

from athena_procurement_arena.policies import BaselineA
from athena_procurement_arena.runner import create_experiment, verify_experiment

timestamp = "2026-01-01T00:00:00+00:00"
scenario = {
    "schema_version": "procurement-arena-scenario-v1",
    "scenario_id": "ordering", "version": "1", "seed": 1,
    "timeline": [timestamp], "evidence": [],
    "truth": {"procurement_episode_id": "p", "outcome": "OPEN"},
}
for evidence_id in ("z", "a"):
    scenario["evidence"].append({
        "evidence_id": evidence_id, "source_id": evidence_id,
        "event_date": timestamp, "document_date": timestamp,
        "verified_available_at": timestamp, "observed_at": timestamp, "claims": {},
    })
with tempfile.TemporaryDirectory() as directory:
    target = Path(directory) / "run"
    create_experiment(json.dumps(scenario), "case.json", target, BaselineA())
    verify_experiment(target)
    print("PASS: unsorted valid evidence retains its actual snapshot order")
