"""Fresh-process inspection must consume saved records without policy execution."""
import contextlib
import io
import json
import sys
from unittest.mock import patch

from athena_procurement_arena import cli

output = io.StringIO()
with (
    patch("athena_procurement_arena.runner.TemporalWorld", side_effect=AssertionError("world executed")),
    patch("athena_procurement_arena.world.TemporalWorld.__init__", side_effect=AssertionError("world constructed")),
    patch("athena_procurement_arena.policies.BaselineA.__call__", side_effect=AssertionError("policy executed")),
    contextlib.redirect_stdout(output),
):
    exit_code = cli.main(["inspect", "--experiment-dir", sys.argv[1]])
payload = json.loads(output.getvalue())
assert exit_code == 0 and payload["status"] == "PASS", payload
print(json.dumps({"status": "PASS", "world_and_policy_execution_disabled": True,
                  "evaluation_status": payload["evaluation"]["status"]}))
