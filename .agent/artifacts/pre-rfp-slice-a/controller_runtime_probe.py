"""Independent real-corpus offline/repeatability acceptance probe."""
import importlib.util
import json
import socket
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("cohort_cli", ROOT / "scripts/run_pre_rfp_cohort.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

cases = sorted((ROOT / "research/pre-rfp-corpus/cases").glob("*/case.json"))
assert len(cases) == 8
with tempfile.TemporaryDirectory(prefix="trailforge-offline-proof-") as temp:
    runs = []
    with patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")), patch(
        "athena_procurement_arena.public_capture.capture_with_firecrawl",
        side_effect=AssertionError("capture forbidden during replay"),
    ):
        for index in (1, 2):
            output = Path(temp) / f"cohort-{index}.json"
            assert cli.main([
                "--mode", "BACKTRACE", "--cases", *map(str, cases),
                "--experiment-root", str(Path(temp) / f"experiments-{index}"),
                "--output", str(output),
            ]) == 0
            runs.append(json.loads(output.read_text(encoding="utf-8")))
    for run in runs:
        assert (run["case_count"], run["positive_count"], run["negative_count"], run["unresolved_count"]) == (8, 4, 1, 3)
        assert run["discovery_credit"] is False
        assert run["supported_historical_lead_count"] == 0
        assert run["unknown_availability_count"] == 11
        assert run["baseline_a_surface_count"] == 0
        assert run["pre_rfp_baseline_surface_count"] == 3
        for result in run["results"]:
            assert result["ledger_verified"] and result["pre_rfp_ledger_verified"]
            assert result["historical_lead_seconds"] is None
            assert result["discovery_credit"] is False
    compared = []
    for left, right in zip(runs[0]["results"], runs[1]["results"], strict=True):
        for key in ("case_hash", "scenario_hash", "experiment_manifest_hash", "pre_rfp_decision_hash"):
            assert left[key] == right[key], (left["case_id"], key)
        a, b = dict(left), dict(right)
        a.pop("experiment_dir")
        b.pop("experiment_dir")
        assert a == b
        compared.append({"case_id": left["case_id"], "pre_rfp_decision_hash": left["pre_rfp_decision_hash"]})
    print(json.dumps({"status": "PASS", "network_blocked": True,
                      "repeat_runs": 2, "cases": compared,
                      "normalization": "Only output experiment_dir differs between separate runs; cohort hashes bind that path."}, indent=2))
