import json
import subprocess

import pytest

from athena_procurement_arena import firecrawl_discovery as discovery


def _fake_run(payload, seen):
    def run(command, **kwargs):
        seen.append((command, kwargs))
        output = command[command.index("-o") + 1]
        with open(output, "w", encoding="utf-8") as stream:
            json.dump(payload, stream)
        return subprocess.CompletedProcess(command, 0, "", "")
    return run


def test_search_normalizes_supported_envelopes_and_retains_raw_response(tmp_path, monkeypatch):
    payload = {"success": True, "id": "job-1", "data": {"web": [
        {"url": "https://example.com/rfp", "title": "RFP", "description": "Open bid", "position": 2}]}}
    calls = []
    monkeypatch.setattr(discovery, "_cli", lambda: ["node", "firecrawl.js"])
    monkeypatch.setattr(discovery.subprocess, "run", _fake_run(payload, calls))
    result = discovery.search("temporary power bid", search_id="safe-id", output_dir=tmp_path,
                              domains=("example.com",), limit=3)
    saved = json.loads((tmp_path / "safe-id-1.search.json").read_text())
    assert result["total_hits"] == 1
    assert saved["raw_response"] == payload
    assert saved["hits"][0]["url"] == "https://example.com/rfp"
    assert "site:example.com" in saved["query"]
    assert calls[0][1]["timeout"] == 180


def test_scrape_passes_ampersand_url_as_single_node_argument_and_retains_freshness_metadata(tmp_path, monkeypatch):
    url = "https://example.com/detail?one=1&two=2"
    payload = {"success": True, "id": "scrape-1", "data": {
        "markdown": "Solicitation closes October 30.",
        "metadata": {"title": "Solicitation", "url": url, "cacheState": "MISS"}}}
    calls = []
    monkeypatch.setattr(discovery, "_cli", lambda: ["node", "firecrawl.js"])
    monkeypatch.setattr(discovery.subprocess, "run", _fake_run(payload, calls))
    capture, capture_path, metadata_path = discovery.scrape(url, capture_id="cap-1", captured_by="reviewer",
        output_dir=tmp_path, source_type="official", max_age_ms=0)
    assert calls[0][0][-1] == url
    metadata = json.loads(metadata_path.read_text())
    assert metadata["freshness_requested_max_age_ms"] == 0
    assert metadata["cache_state"] == "MISS"
    assert metadata["scraped_at"] is None
    assert metadata["raw_response"] == payload
    assert json.loads(capture_path.read_text())["content_sha256"] == capture.content_sha256
    with pytest.raises(FileExistsError):
        discovery.scrape(url, capture_id="cap-1", captured_by="reviewer", output_dir=tmp_path)


@pytest.mark.parametrize("payload", [
    {"success": True, "data": {"results": [{"link": "https://example.com/a", "snippet": "A"}]}},
    {"results": [{"url": "https://example.com/b", "title": "B"}]},
])
def test_search_accepts_known_result_envelope_variants(payload):
    assert len(discovery.normalize_search(payload)) == 1


def test_search_preserves_news_hits_and_provenance():
    hits = discovery.normalize_search({"data": {"web": [{"url": "https://example.com/web"}],
                                       "news": [{"url": "https://example.com/news"}]}})
    assert [item.source_type for item in hits] == ["web", "news"]


def test_search_rejects_path_ids_private_results_and_provider_error_without_echoing(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="query/search_id"):
        discovery.search("query", search_id="../secret", output_dir=tmp_path)
    assert discovery.normalize_search({"data": {"web": [{"url": "http://127.0.0.1/secret"}]}}) == ()
    with pytest.raises(RuntimeError, match="without copying credentials"):
        discovery._json_payload('{"success":false,"error":"secret fc-api-key"}', tmp_path / "missing")
