"""Explicit public URL capture boundary; captured text is not verified truth."""
from __future__ import annotations

import ipaddress
import json
import re
import shutil
import socket
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse

from athena_arena.contracts import canonical_hash


def _public_url(value: str) -> str:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
        raise ValueError("public capture requires a non-local HTTP(S) URL")
    # Host percent-encoding is ambiguous to downstream clients.  Do not allow it
    # to conceal an address that this boundary would otherwise reject.
    if "%" in host:
        raise ValueError("public capture rejects encoded host targets")
    if host == "localhost" or host.endswith((".localhost", ".local")):
        raise ValueError("public capture rejects local network targets")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # inet_aton recognizes legacy IPv4 spellings such as 127.1,
        # 0177.0.0.1, and 2130706433 without doing a DNS lookup.
        try:
            address = ipaddress.ip_address(socket.inet_aton(host))
        except (OSError, ValueError):
            address = None
    if address is not None and not address.is_global:
        raise ValueError("public capture rejects private or non-public IP targets")
    return value


def _aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("captured_at must be timezone-aware")


@dataclass(frozen=True)
class PublicCapture:
    capture_id: str
    source_url: str
    captured_at: datetime
    provider: str
    provider_job_id: str
    captured_by: str
    content: str
    content_sha256: str

    def __post_init__(self) -> None:
        _aware(self.captured_at)
        _public_url(self.source_url)
        if not self.capture_id or not self.provider or not self.captured_by or not self.content:
            raise ValueError("capture_id, provider, captured_by, and content are required")
        expected = sha256(self.content.encode("utf-8")).hexdigest()
        if self.content_sha256 != expected:
            raise ValueError("content_sha256 does not match content")

    @property
    def capture_hash(self) -> str:
        return canonical_hash(self)

    def as_dict(self) -> dict[str, str]:
        return {
            "schema_version": "trailforge-public-capture-v1",
            "capture_id": self.capture_id,
            "source_url": self.source_url,
            "captured_at": self.captured_at.isoformat(),
            "provider": self.provider,
            "provider_job_id": self.provider_job_id,
            "captured_by": self.captured_by,
            "content": self.content,
            "content_sha256": self.content_sha256,
            "capture_hash": self.capture_hash,
        }


def capture_markdown(source_url: str, content: str, *, capture_id: str, captured_by: str,
                     captured_at: datetime | None = None, provider: str = "manual",
                     provider_job_id: str = "") -> PublicCapture:
    """Freeze acquired public markdown without extracting or asserting claims."""
    return PublicCapture(capture_id, _public_url(source_url), captured_at or datetime.now(UTC),
                         provider, provider_job_id, captured_by, content,
                         sha256(content.encode("utf-8")).hexdigest())


def capture_with_firecrawl(source_url: str, *, capture_id: str, captured_by: str,
                           captured_at: datetime | None = None) -> PublicCapture:
    """Run one explicit Firecrawl scrape and freeze its raw markdown response."""
    _public_url(source_url)
    executable = shutil.which("firecrawl.cmd") or shutil.which("firecrawl")
    if not executable:
        raise RuntimeError("Firecrawl CLI is not installed or not on PATH")
    with tempfile.TemporaryDirectory(prefix="trailforge-capture-") as directory:
        raw_path = Path(directory) / "capture.md"
        completed = subprocess.run(
            [executable, "scrape", source_url, "--format", "markdown", "--only-main-content",
             "--no-save-changes", "-o", str(raw_path)],
            capture_output=True, text=True, check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Firecrawl capture failed with exit code {completed.returncode}")
        if not raw_path.exists():
            raise RuntimeError("Firecrawl did not produce a markdown capture")
        match = re.search(r"Scrape ID:\s*(\S+)", completed.stdout)
        return capture_markdown(
            source_url, raw_path.read_text(encoding="utf-8"), capture_id=capture_id,
            captured_by=captured_by, captured_at=captured_at, provider="firecrawl",
            provider_job_id=match.group(1) if match else "",
        )


def write_capture(capture: PublicCapture, path: str | Path) -> None:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"capture output already exists: {destination}")
    destination.write_text(json.dumps(capture.as_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def load_capture(path: str | Path) -> PublicCapture:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema_version") != "trailforge-public-capture-v1":
        raise ValueError("unsupported public capture schema_version")
    capture = capture_markdown(
        raw["source_url"], raw["content"], capture_id=raw["capture_id"],
        captured_by=raw["captured_by"], captured_at=datetime.fromisoformat(raw["captured_at"]),
        provider=raw["provider"], provider_job_id=raw.get("provider_job_id", ""),
    )
    if raw.get("content_sha256") != capture.content_sha256 or raw.get("capture_hash") != capture.capture_hash:
        raise ValueError("public capture hash mismatch")
    return capture
