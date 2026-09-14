"""Selector-driven extraction for HTML listing pages and JSON APIs.

A selector that matches nothing yields an absent field.  Nothing here infers,
normalizes away, or defaults a missing value: an unparsed field must stay unparsed
so the downstream screen reports missing evidence instead of a false qualification.
"""
from __future__ import annotations

import json
import urllib.parse
from typing import Any

from .sources import SourceConfig

FIELD_KEYS = ("title", "url", "buyer", "published", "closes", "solicitation_number", "summary")


class ParseError(RuntimeError):
    """The payload did not match the configured shape; do not fabricate rows."""


def _require_bs4():
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover - exercised via install extra
        raise ParseError(
            "HTML parsing requires beautifulsoup4; install with: pip install -e \".[discovery]\""
        ) from exc
    return BeautifulSoup


def _clean(value: str | None) -> str:
    return " ".join(value.split()) if value else ""


def _select_text(row: Any, selector: str) -> str:
    """Return text for a selector, or an attribute when written as `sel@attr`."""
    if not selector:
        return ""
    target, _, attribute = selector.partition("@")
    found = row.select_one(target.strip()) if target.strip() else row
    if found is None:
        return ""
    if attribute:
        return _clean(found.get(attribute.strip()))
    return _clean(found.get_text(" "))


def _parse_html(config: SourceConfig, text: str) -> tuple[dict[str, str], ...]:
    soup = _require_bs4()(text, "html.parser")
    rows = soup.select(config.selectors["row"])
    records = []
    for row in rows:
        record = {key: _select_text(row, config.selectors.get(key, "")) for key in FIELD_KEYS}
        if record.get("url"):
            record["url"] = urllib.parse.urljoin(config.url, record["url"])
        if any(record.values()):
            records.append(record)
    return tuple(records)


def _dig(payload: Any, path: str) -> Any:
    """Walk a dotted path; `[]` maps the remainder over a list."""
    current = payload
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(current, list):
            if not part.isdigit():
                return None
            current = current[int(part)] if int(part) < len(current) else None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
    return current


def _parse_json(config: SourceConfig, text: str) -> tuple[dict[str, str], ...]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ParseError(f"{config.source_id}: response was not valid JSON") from exc
    rows = _dig(payload, config.selectors["row"])
    if rows is None:
        return ()
    if not isinstance(rows, list):
        raise ParseError(f"{config.source_id}: row selector did not resolve to a list")
    records = []
    for row in rows:
        record = {}
        for key in FIELD_KEYS:
            selector = config.selectors.get(key, "")
            value = _dig(row, selector) if selector else None
            record[key] = _clean(str(value)) if value is not None else ""
        if any(record.values()):
            records.append(record)
    return tuple(records)


def parse_source(config: SourceConfig, text: str) -> tuple[dict[str, str], ...]:
    """Extract raw listing records from one retrieved payload."""
    if config.kind == "html_list":
        return _parse_html(config, text)
    if config.kind == "json_api":
        return _parse_json(config, text)
    raise ParseError(f"unsupported source kind: {config.kind}")
