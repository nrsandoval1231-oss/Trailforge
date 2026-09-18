"""Hash-bound manifests for reviewed project trace cohorts."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from athena_arena.contracts import canonical_hash

from .signal_ledger import ProjectTrace, load_trace


@dataclass(frozen=True)
class TraceCohortManifest:
    cohort_id: str
    assembled_by: str
    assembled_at: datetime
    trace_refs: tuple[dict[str, str], ...]

    def __post_init__(self) -> None:
        if self.assembled_at.tzinfo is None or self.assembled_at.utcoffset() is None:
            raise ValueError("assembled_at must be timezone-aware")
        if not self.cohort_id or not self.assembled_by or not self.trace_refs:
            raise ValueError("cohort_id, assembled_by, and at least one trace are required")
        project_ids = [item["project_id"] for item in self.trace_refs]
        if len(project_ids) != len(set(project_ids)):
            raise ValueError("cohort cannot contain duplicate project IDs")

    @property
    def project_count(self) -> int:
        return len(self.trace_refs)

    @property
    def cohort_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "trailforge-trace-cohort-v1",
            "cohort_id": self.cohort_id,
            "assembled_by": self.assembled_by,
            "assembled_at": self.assembled_at.isoformat(),
            "project_count": self.project_count,
            "trace_refs": [dict(item) for item in self.trace_refs],
            "cohort_hash": self.cohort_hash,
        }


def build_trace_cohort(paths: tuple[str, ...] | list[str], *, cohort_id: str,
                       assembled_by: str, assembled_at: datetime) -> TraceCohortManifest:
    if not paths:
        raise ValueError("at least one trace path is required")
    traces = tuple(load_trace(path) for path in paths)
    refs = tuple({"path": str(path), "project_id": trace.project_id, "trace_hash": trace.trace_hash}
                 for path, trace in zip(paths, traces, strict=True))
    return TraceCohortManifest(cohort_id, assembled_by, assembled_at, refs)


def load_trace_cohort(path: str | Path) -> tuple[TraceCohortManifest, tuple[ProjectTrace, ...]]:
    manifest_path = Path(path)
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "trailforge-trace-cohort-v1":
        raise ValueError("unsupported trace cohort schema_version")
    manifest = TraceCohortManifest(raw["cohort_id"], raw["assembled_by"],
                                   datetime.fromisoformat(raw["assembled_at"]),
                                   tuple(dict(item) for item in raw["trace_refs"]))
    if raw.get("cohort_hash") != manifest.cohort_hash:
        raise ValueError("trace cohort hash mismatch")
    traces = tuple(load_trace(item["path"]) for item in manifest.trace_refs)
    for item, trace in zip(manifest.trace_refs, traces, strict=True):
        if item["project_id"] != trace.project_id or item["trace_hash"] != trace.trace_hash:
            raise ValueError(f"trace cohort member mismatch: {item['path']}")
    return manifest, traces


def write_trace_cohort(manifest: TraceCohortManifest, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"trace cohort output already exists: {destination}")
    destination.write_text(json.dumps(manifest.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
