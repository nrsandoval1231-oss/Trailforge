"""Explicit Firecrawl acquisition commands; no autonomous crawling or follow-up."""
from __future__ import annotations

import argparse
import json
import sys

from .firecrawl_discovery import scrape, search_catalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trailforge-discovery")
    commands = parser.add_subparsers(dest="command", required=True)
    search_parser = commands.add_parser("search", help="run one bounded configured Firecrawl search")
    search_parser.add_argument("--catalog", required=True)
    search_parser.add_argument("--query-id", required=True)
    search_parser.add_argument("--output-dir", required=True)
    capture_parser = commands.add_parser("capture", help="capture one explicitly selected public URL")
    capture_parser.add_argument("--url", required=True)
    capture_parser.add_argument("--capture-id", required=True)
    capture_parser.add_argument("--captured-by", required=True)
    capture_parser.add_argument("--output-dir", required=True)
    capture_parser.add_argument("--source-type", default="web")
    capture_parser.add_argument("--query", default="")
    capture_parser.add_argument("--max-age-ms", type=int, default=0)
    args = parser.parse_args(argv)
    try:
        if args.command == "search":
            result = search_catalog(args.catalog, args.query_id, output_dir=args.output_dir)
        else:
            capture, capture_path, metadata_path = scrape(args.url, capture_id=args.capture_id,
                captured_by=args.captured_by, output_dir=args.output_dir, source_type=args.source_type,
                query=args.query, max_age_ms=args.max_age_ms)
            result = {"status": "PASS", "capture_id": capture.capture_id,
                      "capture_sha256": capture.content_sha256, "capture": str(capture_path),
                      "metadata": str(metadata_path)}
    except (OSError, ValueError, RuntimeError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
