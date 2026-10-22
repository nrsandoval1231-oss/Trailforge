"""Explicit, bounded Firecrawl search and scrape acquisition."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .public_capture import PublicCapture, _public_url, capture_markdown, write_capture

_ARTIFACT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")


def _cli() -> list[str]:
    executable = shutil.which("firecrawl.cmd") or shutil.which("firecrawl")
    if not executable:
        raise RuntimeError("Firecrawl CLI is not installed or not on PATH")
    path = Path(executable)
    if path.suffix.lower() == ".cmd":
        entry = path.parent / "node_modules" / "firecrawl-cli" / "dist" / "index.js"
        node = path.parent / "node.exe"
        if not node.exists():
            node = Path(shutil.which("node.exe") or shutil.which("node") or "")
        if entry.is_file() and node.is_file():
            return [str(node), str(entry)]
        raise RuntimeError("could not safely resolve Firecrawl CLI Node entry point on Windows")
    return [executable]


def _json_payload(stdout: str, output_path: Path) -> dict[str, Any]:
    text = output_path.read_text(encoding="utf-8") if output_path.exists() else stdout
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Firecrawl returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("Firecrawl returned an unexpected response envelope")
    if value.get("success") is False or value.get("error"):
        raise RuntimeError("Firecrawl request failed; inspect provider status without copying credentials into artifacts")
    return value


def _data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        raise RuntimeError("Firecrawl response data is not an object")
    return data


def _write_new(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite acquisition artifact: {path}")
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False,
                              env=os.environ.copy(), timeout=180)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Firecrawl request exceeded the 180-second bound") from exc


@dataclass(frozen=True)
class SearchHit:
    url: str
    title: str
    description: str
    source_type: str
    position: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"url": self.url, "title": self.title, "description": self.description,
                "source_type": self.source_type, "position": self.position}


def normalize_search(payload: dict[str, Any]) -> tuple[SearchHit, ...]:
    """Normalize supported Firecrawl web/news result envelopes; retain raw response separately."""
    data = _data(payload)
    buckets = [(kind, data.get(kind)) for kind in ("web", "news", "images") if data.get(kind) is not None]
    if not buckets:
        buckets = [("web", data.get("results", payload.get("results", [])))]
    hits = []
    for kind, results in buckets:
        if results is None:
            continue
        if not isinstance(results, list):
            raise RuntimeError("Firecrawl search result list is malformed")
        for index, item in enumerate(results):
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("link")
            if not isinstance(url, str):
                continue
            try:
                _public_url(url)
            except ValueError:
                continue
            hits.append(SearchHit(url=url, title=str(item.get("title") or ""),
                                  description=str(item.get("description") or item.get("snippet") or ""),
                                  source_type=str(item.get("source_type") or item.get("source") or kind),
                                  position=item.get("position", index + 1)))
    return tuple(hits)


def search(query: str, *, search_id: str, output_dir: str | Path, limit: int = 10,
           sources: tuple[str, ...] = ("web",), categories: tuple[str, ...] = (),
           domains: tuple[str, ...] = ()) -> dict[str, Any]:
    """Run one bounded CLI search per configured domain and preserve full provider JSON."""
    if not query.strip() or not _ARTIFACT_ID.fullmatch(search_id) or not 1 <= limit <= 100:
        raise ValueError("query/search_id are required and limit must be 1..100")
    if not sources or any(item not in {"web", "news", "images"} for item in sources):
        raise ValueError("sources must be web, news, or images")
    if len(domains) > 20:
        raise ValueError("a single search is limited to 20 configured domains")
    if any(not domain or "/" in domain or ":" in domain for domain in domains):
        raise ValueError("domains must contain hostnames only")
    root = Path(output_dir)
    recorded: list[dict[str, Any]] = []
    targets = domains or ("",)
    for index, domain in enumerate(targets):
        effective_query = f"site:{domain} {query}" if domain else query
        stem = f"{search_id}-{index + 1}"
        artifact = root / f"{stem}.search.json"
        if artifact.exists():
            raise FileExistsError(f"refusing to overwrite acquisition artifact: {artifact}")
        with tempfile.TemporaryDirectory(prefix="trailforge-search-") as directory:
            raw_path = Path(directory) / "response.json"
            command = [*_cli(), "search", "--limit", str(limit), "--sources", ",".join(sources), "--json",
                       "--no-highlights", "-o", str(raw_path)]
            if categories:
                command.extend(("--categories", ",".join(categories)))
            command.extend(("--", effective_query))  # a query starting with "-" is never read as an option
            completed = _run(command)
            if completed.returncode:
                raise RuntimeError(f"Firecrawl search failed with exit code {completed.returncode}")
            payload = _json_payload(completed.stdout, raw_path)
        hits = normalize_search(payload)
        envelope = {"schema_version": "trailforge-firecrawl-search-v1", "search_id": f"{search_id}-{index + 1}",
                    "query": effective_query, "requested_query": query, "domain": domain or None,
                    "sources": list(sources), "categories": list(categories), "limit": limit,
                    "retrieved_at": datetime.now(UTC).isoformat(), "provider": "firecrawl",
                    "provider_job_id": payload.get("id") or _data(payload).get("id"),
                    "hits": [hit.as_dict() for hit in hits], "raw_response": payload}
        _write_new(artifact, envelope)
        recorded.append({"path": str(artifact), "hit_count": len(hits), "query": effective_query})
    return {"schema_version": "trailforge-firecrawl-search-set-v1", "search_id": search_id,
            "queries": recorded, "total_hits": sum(item["hit_count"] for item in recorded)}


def load_catalog(path: str | Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != "trailforge-discovery-catalog-v1":
        raise ValueError("unsupported discovery catalog")
    entries = raw.get("queries")
    if not isinstance(entries, list):
        raise ValueError("discovery catalog queries must be a list")
    result = {}
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("id") or not entry.get("query"):
            raise ValueError("catalog entries require id and query")
        if entry["id"] in result:
            raise ValueError(f"duplicate discovery query id: {entry['id']}")
        result[entry["id"]] = entry
    return result


def search_catalog(catalog_path: str | Path, query_id: str, *, output_dir: str | Path) -> dict[str, Any]:
    entry = load_catalog(catalog_path).get(query_id)
    if not entry:
        raise ValueError(f"unknown catalog query id: {query_id}")
    return search(entry["query"], search_id=query_id, output_dir=output_dir,
                  limit=int(entry.get("limit", 10)), sources=tuple(entry.get("sources", ["web"])),
                  categories=tuple(entry.get("categories", [])), domains=tuple(entry.get("domains", [])))


def scrape(source_url: str, *, capture_id: str, captured_by: str, output_dir: str | Path,
           source_type: str = "web", query: str = "", max_age_ms: int = 0) -> tuple[PublicCapture, Path, Path]:
    """Scrape a selected public URL and persist raw provider metadata and immutable Markdown capture."""
    _public_url(source_url)
    if not _ARTIFACT_ID.fullmatch(capture_id) or not captured_by.strip() or max_age_ms < 0:
        raise ValueError("capture_id/captured_by are required and max_age_ms cannot be negative")
    root = Path(output_dir)
    capture_path = root / f"{capture_id}.capture.json"
    metadata_path = root / f"{capture_id}.acquisition.json"
    if capture_path.exists() or metadata_path.exists():
        raise FileExistsError("refusing to overwrite existing capture artifacts")
    with tempfile.TemporaryDirectory(prefix="trailforge-scrape-") as directory:
        raw_path = Path(directory) / "response.json"
        command = [*_cli(), "scrape", "--format", "markdown", "--only-main-content", "--max-age",
                   str(max_age_ms), "--json", "-o", str(raw_path), source_url]
        completed = _run(command)
        if completed.returncode:
            raise RuntimeError(f"Firecrawl scrape failed with exit code {completed.returncode}")
        payload = _json_payload(completed.stdout, raw_path)
    data = _data(payload)
    markdown = data.get("markdown")
    if not isinstance(markdown, str) or not markdown.strip():
        raise RuntimeError("Firecrawl scrape returned no Markdown content")
    completed_at = datetime.now(UTC)
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    capture = capture_markdown(source_url, markdown, capture_id=capture_id, captured_by=captured_by,
                               provider="firecrawl", provider_job_id=str(payload.get("id") or metadata.get("scrapeId") or ""))
    root.mkdir(parents=True, exist_ok=True)
    write_capture(capture, capture_path)
    _write_new(metadata_path, {"schema_version": "trailforge-firecrawl-acquisition-v1", "capture_id": capture_id,
        "source_url": source_url, "query": query, "source_type": source_type, "title": metadata.get("title"),
        "domain": metadata.get("url") or source_url, "completed_at": completed_at.isoformat(),
        "retrieved_at": completed_at.isoformat(),
        "freshness_requested_max_age_ms": max_age_ms, "scraped_at": metadata.get("scrapedAt") or metadata.get("scraped_at"),
        "cache_state": metadata.get("cacheState") or metadata.get("cache_state") or "UNKNOWN",
        "cached_at": metadata.get("cachedAt") or metadata.get("cached_at"),
        "provider_job_id": capture.provider_job_id, "capture_sha256": capture.content_sha256,
        "raw_response": payload})
    return capture, capture_path, metadata_path
