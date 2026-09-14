"""Declarative source definitions: adding a jurisdiction is configuration."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SOURCE_KINDS = frozenset({"html_list", "json_api"})
CONFIG_DIR = Path(__file__).resolve().parent / "configs"


@dataclass(frozen=True)
class SourceConfig:
    """How to reach one listing index and locate records inside it.

    `selectors` are CSS selectors for `html_list`, or dotted JSON paths for
    `json_api`.  `row` locates each record; the remaining keys locate fields
    within a record.  A selector that matches nothing yields an absent field,
    never a guess.
    """

    source_id: str
    name: str
    url: str
    kind: str
    jurisdiction: str = ""
    selectors: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    api_key_env: str = ""
    rate_limit_seconds: float = 2.0
    enabled: bool = True
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.source_id or not self.name:
            raise ValueError("source_id and name are required")
        if self.kind not in SOURCE_KINDS:
            raise ValueError(f"kind must be one of {sorted(SOURCE_KINDS)}")
        if not self.url.startswith("https://"):
            raise ValueError("source url must be https")
        if "row" not in self.selectors:
            raise ValueError("selectors must include a 'row' entry")
        if self.rate_limit_seconds < 0:
            raise ValueError("rate_limit_seconds cannot be negative")

    @property
    def requires_api_key(self) -> bool:
        return bool(self.api_key_env)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id, "name": self.name, "url": self.url,
            "kind": self.kind, "jurisdiction": self.jurisdiction,
            "selectors": dict(self.selectors), "headers": dict(self.headers),
            "params": dict(self.params), "api_key_env": self.api_key_env,
            "rate_limit_seconds": self.rate_limit_seconds, "enabled": self.enabled,
            "notes": self.notes,
        }


def source_from_mapping(raw: dict[str, Any]) -> SourceConfig:
    known = {item.name for item in SourceConfig.__dataclass_fields__.values()}
    unknown = sorted(set(raw) - known)
    if unknown:
        raise ValueError(f"unknown source config keys: {', '.join(unknown)}")
    return SourceConfig(**raw)


def load_sources(path: str | Path) -> tuple[SourceConfig, ...]:
    """Load source configs from a JSON file or a directory of JSON files."""
    target = Path(path)
    files = sorted(target.glob("*.json")) if target.is_dir() else [target]
    configs: list[SourceConfig] = []
    for item in files:
        raw = json.loads(item.read_text(encoding="utf-8"))
        entries = raw if isinstance(raw, list) else [raw]
        configs.extend(source_from_mapping(entry) for entry in entries)
    ids = [item.source_id for item in configs]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise ValueError(f"duplicate source_id: {', '.join(duplicates)}")
    return tuple(configs)


def builtin_sources(*, enabled_only: bool = True) -> tuple[SourceConfig, ...]:
    """Load the configs shipped with the package."""
    if not CONFIG_DIR.is_dir():
        return ()
    configs = load_sources(CONFIG_DIR)
    return tuple(item for item in configs if item.enabled) if enabled_only else configs
