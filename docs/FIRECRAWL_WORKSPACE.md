# Firecrawl opportunity workspace

The two commands make a bounded path from public discovery to a local, reviewable opportunity record. They do not contact buyers or submit proposals.

```powershell
uv run trailforge-discovery search --catalog config/discovery.catalog.json --query-id temporary-generation-rfp --output-dir .trailforge-runs/acquisition/searches
uv run trailforge-discovery capture --url https://example.com/selected-public-source --capture-id source-001 --captured-by operator --source-type official-source --query "temporary generation RFP" --max-age-ms 0 --output-dir .trailforge-runs/acquisition/captures
uv run trailforge-opportunity import --workspace .trailforge-runs/operator --input .trailforge-runs/operator/inputs/opportunity.json
uv run trailforge-opportunity render --workspace .trailforge-runs/operator --output .trailforge-runs/operator/index.html
```

Create `.trailforge-runs/operator/inputs/opportunity.json` after capturing and reviewing a public source. Replace each quote with an exact span from the selected capture; leave unsupported values `null`.

```json
{
  "schema_version": "trailforge-opportunity-input-v1",
  "opportunity_id": "reviewed-project-001",
  "kind": "PRE_RFP_PROJECT",
  "title": "Example project",
  "identity": {"organization": "Example owner", "project": "Example site", "location": "Example, NY"},
  "reviewed_by": "operator",
  "reviewed_at": "2026-10-02T12:00:00Z",
  "sources": [{"capture_file": "../../acquisition/captures/source-001.capture.json"}],
  "field_evidence": {
    "title": {"capture_file": "../../acquisition/captures/source-001.capture.json", "quote": "Example project"},
    "identity.organization": {"capture_file": "../../acquisition/captures/source-001.capture.json", "quote": "Example owner"},
    "identity.project": {"capture_file": "../../acquisition/captures/source-001.capture.json", "quote": "Example site"},
    "identity.location": {"capture_file": "../../acquisition/captures/source-001.capture.json", "quote": "Example, NY"}
  },
  "requirements": {},
  "documents": [],
  "notes": "Human-reviewed intake; verify all claims against the retained source."
}
```

The catalog is editable JSON. Each query sets its own result limit, source types, optional Firecrawl categories, and optional host restrictions. Empty `domains` means broad web search. A query returns normalized public URLs plus the complete provider response in a new, no-overwrite artifact. Capture accepts one explicitly selected public HTTP(S) URL and saves an immutable `PublicCapture` plus its raw Firecrawl response and acquisition metadata. The Windows CLI path resolves directly to Node and the installed Firecrawl entry point so URLs with `&` remain one argument.

An import JSON uses `schema_version: "trailforge-opportunity-input-v1"`, `kind: "PRE_RFP_PROJECT"` or `"ACTIVE_RFP"`, `opportunity_id`, title and identity fields, review identity/time, and a `sources` list with relative `capture_file` paths. Each known title, identity fact, date, deadline, and requirement requires a corresponding `field_evidence` or `requirement_quotes` object containing the capture path and a literal quote found in that capture. Date-only publication dates preserve date precision; deadline timestamps require an explicit timezone. Optional original documents may be retained using `documents[].original_file` and `documents[].sha256`.

The operator workspace stores captures under their capture hashes and retained originals under their file hashes. Every rendered record and retained file is checked against its saved hash. New captures are never overwritten. An exact cited deadline plus capture-bound acquisition metadata (`max-age-ms 0`, a recent retrieval time, and a confirmed cache miss/bypass/refresh) is required before an RFP can show `OPEN_AS_OF_PUBLIC_SOURCE`; missing, contradictory, unknown-cache, nonzero-age, or stale provenance remains `UNKNOWN`/`NEEDS_REVIEW`. Expired deadlines display `EXPIRED`, and amendment status remains `UNKNOWN` without source evidence. The strict 2G screen keeps raw reason codes, treats program aggregates separately from per-project requirements, and maps a rejected screen to `NOT_FIT`. A passing mechanical screen remains pending human review.

Drafts live in editable `drafts/<opportunity-id>.json`; rendering escapes source text and shows source excerpts, hashes, retained-file links, requirements, missing information, notes, unanswered questions, and next action. Ambiguous project identities remain separate. Matching stable identities merge source history; contradictory requirement values become `CONFLICT - HUMAN REVIEW REQUIRED`. Early-project and RFP records remain separate from verified simulation fixtures.
