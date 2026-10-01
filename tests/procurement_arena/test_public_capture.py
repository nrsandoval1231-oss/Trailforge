import json
from datetime import UTC, datetime
from hashlib import sha256

import pytest

from athena_procurement_arena import (
    capture_markdown,
    capture_with_firecrawl,
    load_capture,
    write_capture,
)


def test_capture_freezes_content_and_round_trips(tmp_path):
    capture = capture_markdown(
        "https://example.com/project", "# Project\n", capture_id="cap-1", captured_by="operator",
        captured_at=datetime(2026, 9, 17, tzinfo=UTC),
    )
    path = tmp_path / "capture.json"
    write_capture(capture, path)
    loaded = load_capture(path)
    assert loaded.capture_hash == capture.capture_hash
    assert loaded.content_sha256 == sha256(b"# Project\n").hexdigest()
    with pytest.raises(FileExistsError):
        write_capture(capture, path)


def test_capture_rejects_non_public_targets():
    with pytest.raises(ValueError, match=r"HTTP\(S\)"):
        capture_markdown("file:///secret", "content", capture_id="cap-1", captured_by="operator")
    with pytest.raises(ValueError, match="non-public"):
        capture_markdown("http://192.168.1.10/source", "content", capture_id="cap-1", captured_by="operator")
    for url in ("http://172.17.0.1/source", "http://[fd00::1]/source", "http://127.0.0.1/source",
                "http://user:password@example.com/source", "http://server.localhost/source"):
        with pytest.raises(ValueError):
            capture_markdown(url, "content", capture_id="cap-1", captured_by="operator")


def test_firecrawl_capture_is_explicit_and_raw(monkeypatch, tmp_path):
    def fake_run(command, **kwargs):
        output_path = command[-1]
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write("# Raw source\n")
        return type("Result", (), {"returncode": 0, "stdout": "Scrape ID: job-123\n"})()

    monkeypatch.setattr("athena_procurement_arena.public_capture.subprocess.run", fake_run)
    monkeypatch.setattr("athena_procurement_arena.public_capture.shutil.which", lambda name: "firecrawl.cmd")
    capture = capture_with_firecrawl("https://example.com/source", capture_id="cap-2", captured_by="operator")
    assert capture.provider == "firecrawl"
    assert capture.provider_job_id == "job-123"
    assert capture.content == "# Raw source\n"


def test_capture_hash_tampering_is_rejected(tmp_path):
    capture = capture_markdown("https://example.com", "source", capture_id="cap-3", captured_by="operator")
    path = tmp_path / "capture.json"
    write_capture(capture, path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["content"] = "altered"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch|does not match"):
        load_capture(path)
