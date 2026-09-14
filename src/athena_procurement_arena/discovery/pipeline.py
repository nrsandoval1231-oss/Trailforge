"""Run configured sources and return a ranked review queue.

One source failing never fails the sweep: its error is recorded and the remaining
sources still run, because a broad scrape over many fragile sites is expected to
have partial outages. A source that errors contributes no rows -- never inferred
or stale ones.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .candidates import ReviewCandidate
from .fetch import Fetcher, FetchError
from .parse import ParseError, parse_source
from .sources import SourceConfig, builtin_sources


@dataclass(frozen=True)
class SourceOutcome:
    source_id: str
    status: str
    candidates: tuple[ReviewCandidate, ...] = ()
    error: str = ""
    rows: int = 0
    cache_path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"source_id": self.source_id, "status": self.status, "rows": self.rows,
                "candidates": len(self.candidates), "error": self.error,
                "cache_path": self.cache_path}


def _resolve_headers(config: SourceConfig) -> dict[str, str]:
    headers = dict(config.headers)
    if config.requires_api_key:
        key = os.environ.get(config.api_key_env, "")
        if not key:
            raise FetchError(
                f"{config.source_id} requires the {config.api_key_env} environment variable")
        headers = {name: value.replace("{api_key}", key) for name, value in headers.items()}
    return headers


def _resolve_params(config: SourceConfig) -> dict[str, str]:
    if not config.requires_api_key:
        return dict(config.params)
    key = os.environ.get(config.api_key_env, "")
    return {name: value.replace("{api_key}", key) for name, value in config.params.items()}


def run_source(config: SourceConfig, fetcher: Fetcher) -> SourceOutcome:
    """Retrieve and parse one source, converting failures into a recorded outcome."""
    try:
        headers = _resolve_headers(config)
        result = fetcher.fetch(config.url, headers=headers, params=_resolve_params(config),
                               rate_limit_seconds=config.rate_limit_seconds)
        records = parse_source(config, result.text)
    except (FetchError, ParseError) as exc:
        return SourceOutcome(config.source_id, "ERROR", error=str(exc))

    candidates = []
    for record in records:
        try:
            candidates.append(ReviewCandidate(
                source_id=config.source_id, title=record.get("title", ""),
                url=record.get("url") or config.url, retrieved_at=result.retrieved_at,
                buyer=record.get("buyer", ""), published=record.get("published", ""),
                closes=record.get("closes", ""),
                solicitation_number=record.get("solicitation_number", ""),
                summary=record.get("summary", ""), jurisdiction=config.jurisdiction,
                cache_path=result.cache_path, raw=dict(record),
            ))
        except ValueError:
            continue  # A row with neither title nor summary carries no reviewable content.
    return SourceOutcome(config.source_id, "OK", tuple(candidates),
                         rows=len(records), cache_path=result.cache_path)


def discover(
    configs: tuple[SourceConfig, ...] | None = None, *, cache_dir: str | Path | None = None,
    fetcher: Fetcher | None = None, minimum_score: int = 1, limit: int = 50,
    respect_robots: bool = True,
) -> dict[str, Any]:
    """Sweep every configured source and return a ranked, deduplicated queue."""
    configs = configs if configs is not None else builtin_sources()
    if not configs:
        return {"status": "PASS", "mode": "discover", "sources": [], "candidates": [],
                "count": 0, "note": "no enabled sources configured"}
    active = fetcher or Fetcher(cache_dir=cache_dir, respect_robots=respect_robots)

    outcomes = [run_source(config, active) for config in configs]
    seen: set[str] = set()
    ranked: list[ReviewCandidate] = []
    for outcome in outcomes:
        for candidate in outcome.candidates:
            key = candidate.url or f"{candidate.source_id}:{candidate.title}"
            if key in seen:
                continue
            seen.add(key)
            if candidate.triage.score >= minimum_score:
                ranked.append(candidate)
    ranked.sort(key=lambda item: (-item.triage.score, item.source_id, item.title))

    return {
        "status": "PASS",
        "mode": "discover",
        "sources": [outcome.as_dict() for outcome in outcomes],
        "errors": [outcome.source_id for outcome in outcomes if outcome.status == "ERROR"],
        "count": len(ranked[:limit]),
        "total_ranked": len(ranked),
        "candidates": [item.as_dict() for item in ranked[:limit]],
        "note": "AWAITING_REVIEW: ranking orders attention and qualifies nothing",
    }


def write_queue(result: dict[str, Any], path: str | Path) -> str:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return str(destination)
