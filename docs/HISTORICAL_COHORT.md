# HC-001 historical cohort adapter

Run from the repository root with `python scripts/run_hc001.py INPUT.json NEW_EMPTY_OUTPUT_DIR`. The runner performs no network access. It validates cited captures and excerpts, writes canonical eligible traces plus deterministic `report.json` and `report.md`, and leaves input research records untouched. The JSON report binds the raw input bytes with SHA-256.

## Input contract

The input is JSON with `schema_version: "trailforge-historical-cohort-input-v1"`, a `cohort_id`, a fixed `policy`, and a `projects` array. Each project has a unique `project_id`, `identity_status`, `identity_basis`, `signals`, an optional `conventional_milestone_signal_id`, and a `buyer_path` object.

Policy requires `target_signal_type`, non-empty `early_signal_types`, and a written `selection_basis`. These values are replayed as supplied; the adapter does not tune them.

Each signal includes `signal_id`, `signal_type`, `title`, `source_url`, `source_capture_path`, `source_sha256`, and an exact `excerpt`. Capture paths are relative to the input JSON directory. The referenced TrailForge public-capture JSON must pass its hash check, the URL must match, the excerpt must occur verbatim, and `source_sha256` must equal the capture content hash.

`published_at`, `published_date_precision`, `published_date_excerpt`, and `published_date_basis` are diagnostic only. The excerpt must occur verbatim in the source capture. Basis is either `DISPLAYED_SOURCE_DATE_NOT_VERIFIED_AVAILABILITY` or `DOCUMENT_ISSUE_DATE_NOT_WEB_PUBLICATION`. Precision is `day` or `instant`; a day is represented as a calendar-day interval with timezone `UNKNOWN`. These intervals never establish historical availability and are never fed to the backtest.

Missing availability remains `UNKNOWN`. A supplied `available_at` requires one of `ARCHIVED_CONTENT`, `OFFICIAL_PUBLICATION_TIMESTAMP`, or `CURRENT_CAPTURE`, plus a validated capture, exact `availability_excerpt`, and exact `availability_time_excerpt`. `ARCHIVED_CONTENT` is accepted only when the capture URL is a Wayback URL, the embedded 14-digit UTC time equals `available_at`, the embedded original URL equals the cited source URL, and both the availability excerpt and signal excerpt occur in captured content. `OFFICIAL_PUBLICATION_TIMESTAMP` requires the capture URL to equal the cited source URL and an exact timezone-aware timestamp excerpt equal to `available_at`. `CURRENT_CAPTURE` remains `UNKNOWN`. The adapter checks structured identity and timestamp bindings; whether the cited excerpt semantically proves the event or publication claim remains subject to independent human audit. A retrospective event date or publication date alone does not qualify. Contradictory availability is downgraded to `UNKNOWN`.

The conventional milestone must point to a supplied signal with the fixed target type. Buyer evidence capture and exact excerpt are always validated, even when availability is absent. The stated organization is preserved separately; the supported organization remains `UNKNOWN` unless historical buyer availability is evidenced at or before the first valid policy surface. An identified organization alone does not establish buyer-path availability.

## Report semantics

Only resolved-identity projects' explicitly supported policy early signals and the selected target are converted to `ProjectSignal` records, with `observed_at` set to supported `available_at`, then passed through existing `backtest_traces`. A project with no such signal remains in `cases` but has no canonical trace. `eligible_trace_count` and replay denominator make that boundary visible. Replay uses only the explicitly selected target signal. Earliest supported signal, milestone and buyer-path evidence remain inspectable per project; all unresolved projects and signals remain in the report.

The trace ledger's required `verified_by` field is populated with `agent-assisted-extraction-pending-independent-semantic-review`. This identifies the extraction process; it does not assert a human reviewer or approval. HC-001 is a small convenience cohort and makes no predictive-quality, false-positive-rate, or signal-promotion claim. No contact or submission action follows from this output.

## Complete example

The complete input contract and cited capture set are in [`research/hc-001/cohort-input.json`](../research/hc-001/cohort-input.json). Run that exact five-project example with `uv run --frozen --extra dev python scripts/run_hc001.py research/hc-001/cohort-input.json .firecrawl/hc001-output`, using a new or empty output directory.
