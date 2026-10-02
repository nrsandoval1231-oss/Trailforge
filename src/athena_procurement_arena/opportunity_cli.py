"""Command line for the local opportunity workspace."""
from __future__ import annotations

import argparse
import json
import sys

from .opportunity_workspace import import_opportunity, render_workspace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trailforge-opportunity")
    commands = parser.add_subparsers(dest="command", required=True)
    importer = commands.add_parser("import", help="import reviewed, source-cited opportunity evidence")
    importer.add_argument("--workspace", required=True)
    importer.add_argument("--input", required=True)
    renderer = commands.add_parser("render", help="render the local operator workspace as static HTML")
    renderer.add_argument("--workspace", required=True)
    renderer.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "import":
            record = import_opportunity(args.input, args.workspace)
            result = {"status": "PASS", "opportunity_id": record["opportunity_id"],
                      "kind": record["kind"], "identity_resolution": record["identity_resolution"],
                      "qualification": record["qualification"], "workspace": args.workspace}
        else:
            target = render_workspace(args.workspace, args.output)
            result = {"status": "PASS", "output": str(target)}
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, RuntimeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
