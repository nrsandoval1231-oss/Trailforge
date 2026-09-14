"""Polite HTTP retrieval with robots.txt compliance and on-disk raw caching.

Scraping public procurement pages is a durable relationship with the hosts who
publish them, so retrieval is conservative by default: robots.txt is honored,
requests are rate limited per host, and every response body is written to disk
unmodified.  That cached file is what `capture` fingerprints, which keeps the
provenance chain intact from retrieval through to a verified record.
"""
from __future__ import annotations

import hashlib
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.robotparser import RobotFileParser

USER_AGENT = "TrailforgeResearchBot/0.1 (procurement research; contact via repository)"
DEFAULT_TIMEOUT = 30.0
MAX_BYTES = 8 * 1024 * 1024


class FetchError(RuntimeError):
    """Retrieval failed or was refused; callers must not substitute a guess."""


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    body: bytes
    retrieved_at: str
    content_type: str = ""
    cache_path: str | None = None

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.body).hexdigest()

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


class RobotsPolicy:
    """Cache robots.txt per host and refuse disallowed paths."""

    def __init__(self, *, user_agent: str = USER_AGENT, timeout: float = 10.0,
                 allow_on_error: bool = True) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        # A missing or unreachable robots.txt conventionally means unrestricted.
        self.allow_on_error = allow_on_error
        self._cache: dict[str, RobotFileParser | None] = {}

    def _parser(self, url: str) -> RobotFileParser | None:
        parts = urllib.parse.urlsplit(url)
        root = f"{parts.scheme}://{parts.netloc}"
        if root not in self._cache:
            parser = RobotFileParser()
            parser.set_url(f"{root}/robots.txt")
            try:
                request = urllib.request.Request(
                    f"{root}/robots.txt", headers={"User-Agent": self.user_agent})
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    parser.parse(response.read().decode("utf-8", errors="replace").splitlines())
            except (urllib.error.URLError, OSError, ValueError):
                self._cache[root] = None
                return None
            self._cache[root] = parser
        return self._cache[root]

    def allows(self, url: str) -> bool:
        parser = self._parser(url)
        if parser is None:
            return self.allow_on_error
        return parser.can_fetch(self.user_agent, url)


class Fetcher:
    """Rate-limited, robots-respecting retrieval that caches raw bytes."""

    def __init__(self, *, cache_dir: str | Path | None = None, user_agent: str = USER_AGENT,
                 timeout: float = DEFAULT_TIMEOUT, robots: RobotsPolicy | None = None,
                 respect_robots: bool = True, sleep=time.sleep) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.user_agent = user_agent
        self.timeout = timeout
        self.respect_robots = respect_robots
        self.robots = robots or RobotsPolicy(user_agent=user_agent)
        self._sleep = sleep
        self._last_request: dict[str, float] = {}

    def _throttle(self, url: str, rate_limit_seconds: float) -> None:
        host = urllib.parse.urlsplit(url).netloc
        previous = self._last_request.get(host)
        now = time.monotonic()
        if previous is not None:
            remaining = rate_limit_seconds - (now - previous)
            if remaining > 0:
                self._sleep(remaining)
        self._last_request[host] = time.monotonic()

    def _cache_path(self, url: str, retrieved_at: str) -> Path | None:
        if self.cache_dir is None:
            return None
        host = urllib.parse.urlsplit(url).netloc.replace(":", "_")
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        stamp = retrieved_at.replace(":", "").replace("-", "").replace("+", "p")
        return self.cache_dir / host / f"{stamp}-{digest}.raw"

    def fetch(self, url: str, *, headers: dict[str, str] | None = None,
              params: dict[str, str] | None = None, rate_limit_seconds: float = 2.0) -> FetchResult:
        if not url.startswith("https://"):
            raise FetchError(f"refusing non-https retrieval: {url}")
        target = url
        if params:
            separator = "&" if urllib.parse.urlsplit(url).query else "?"
            target = f"{url}{separator}{urllib.parse.urlencode(params)}"
        if self.respect_robots and not self.robots.allows(target):
            raise FetchError(f"robots.txt disallows retrieval: {target}")

        self._throttle(target, rate_limit_seconds)
        request = urllib.request.Request(
            target, headers={"User-Agent": self.user_agent, "Accept": "*/*", **(headers or {})})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read(MAX_BYTES + 1)
                status = response.status
                content_type = response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            raise FetchError(f"HTTP {exc.code} for {target}") from exc
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise FetchError(f"retrieval failed for {target}: {exc}") from exc
        if len(body) > MAX_BYTES:
            raise FetchError(f"response exceeded {MAX_BYTES} bytes: {target}")

        retrieved_at = datetime.now(UTC).isoformat()
        cache_path = self._cache_path(target, retrieved_at)
        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(body)
        return FetchResult(target, status, body, retrieved_at, content_type,
                           str(cache_path) if cache_path else None)
