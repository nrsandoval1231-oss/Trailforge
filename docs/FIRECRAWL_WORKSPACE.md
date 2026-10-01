# Firecrawl opportunity workspace

The two commands make a bounded path from public discovery to a local, reviewable opportunity record. They do not contact buyers or submit proposals.

```powershell
uv run trailforge-discovery search --catalog config/discovery.catalog.json --query-id temporary-generation-rfp --output-dir research/acquisition/searches
uv run trailforge-discovery capture --url https://example.com/selected-public-source --capture-id source-001 --captured-by operator --source-type official-source --query "temporary generation RFP" --max-age-ms 0 --output-dir research/acquisition/captures
uv run trailforge-opportunity import --workspace research/operator-workspace --input research/operator-workspace/inputs/opportunity.json
uv run trailforge-opportunity render --workspace research/operator-workspace --output research/operator-workspace/index.html
```

The catalog is editable JSON. Each query sets its own result limit, source types, optional Firecrawl categories, and optional host restrictions. Empty `domains` means broad web search. A query returns normalized public URLs plus the complete provider response in a new, no-overwrite artifact. Capture accepts one explicitly selected public HTTP(S) URL and saves an immutable `PublicCapture` plus its raw Firecrawl response and acquisition metadata. The Windows CLI path resolves directly to Node and the installed Firecrawl entry point so URLs with `&` remain one argument.

An import JSON uses `schema_version: "trailforge-opportunity-input-v1"`, `kind: "PRE_RFP_PROJECT"` or `"ACTIVE_RFP"`, `opportunity_id`, title and identity fields, review identity/time, and a `sources` list with relative `capture_file` paths. Each known title, identity fact, date, deadline, and requirement requires a corresponding `field_evidence` or `requirement_quotes` object containing the capture path and a literal quote found in that capture. Date-only publication dates preserve date precision; deadline timestamps require an explicit timezone. Optional original documents may be retained using `documents[].original_file` and `documents[].sha256`.

The operator workspace stores captures under their capture hashes and retained originals under their file hashes. Every rendered record and retained file is checked against its saved hash. New captures are never overwritten. A sufficiently recent acquisition (`max-age-ms 0`) must support the exact cited deadline before an RFP can show `OPEN_AS_OF_PUBLIC_SOURCE`; expired deadlines display `EXPIRED`, and amendment status remains `UNKNOWN` without source evidence. The strict 2G screen keeps raw reason codes, treats program aggregates separately from per-project requirements, and maps a rejected screen to `NOT_FIT`. A passing mechanical screen remains pending human review.

Drafts live in editable `drafts/<opportunity-id>.json`; rendering escapes source text and shows source excerpts, hashes, retained-file links, requirements, missing information, notes, unanswered questions, and next action. Ambiguous project identities remain separate. Matching stable identities merge source history; contradictory requirement values become `CONFLICT - HUMAN REVIEW REQUIRED`. Early-project and RFP records remain separate from verified simulation fixtures.
