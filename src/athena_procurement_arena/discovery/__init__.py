"""Multi-source opportunity discovery.

Discovery proposes; a human disposes.  Nothing in this package can mark evidence
verified: it emits ranked *review candidates* carrying the raw retrieved bytes,
and the existing `capture` path -- which requires a human reviewer -- remains the
only way a record becomes a VERIFIED fixture.

Site coverage is configuration, not code.  Adding a jurisdiction means adding a
`SourceConfig` entry with selectors, so breadth does not multiply the number of
parsers to maintain.
"""
from __future__ import annotations

from .candidates import ReviewCandidate, candidate_to_capture_request
from .fetch import Fetcher, FetchError, FetchResult, RobotsPolicy
from .parse import ParseError, parse_source
from .sources import SourceConfig, builtin_sources, load_sources
from .triage import TRIAGE_TERMS, triage_score

__all__ = [
    "TRIAGE_TERMS",
    "FetchError",
    "FetchResult",
    "Fetcher",
    "ParseError",
    "ReviewCandidate",
    "RobotsPolicy",
    "SourceConfig",
    "builtin_sources",
    "candidate_to_capture_request",
    "load_sources",
    "parse_source",
    "triage_score",
]
