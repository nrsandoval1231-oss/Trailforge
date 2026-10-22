# Find leads

The operator app's **Find** tab runs live public-web searches through the existing Firecrawl plumbing and keeps the hits as **unreviewed leads** that you triage into *Potential RFPs* and *Early projects*. It finds candidates; it does not verify, rank commercial value, contact anyone, or send anything.

```powershell
uv run --python 3.11 trailforge-ui --saved-only            # then open http://127.0.0.1:8765/app#/find
uv run --python 3.11 trailforge-ui --saved-only --discovery-catalog path\to\catalog.json
```

Requires the authenticated Firecrawl CLI (`firecrawl --status`). Without it a run reports a clear error in the Find tab instead of failing.

## Workflow
1. **Run searches.** Tick catalog queries (from `config/discovery.catalog.json`, or `--discovery-catalog PATH`) and/or type one custom query. The panel shows the estimate (`≈N searches ... Uses Firecrawl credits`); nothing runs until you click *Confirm and run*. Searches run in the background and the tab polls progress. A failed search is reported and the rest continue (a catalog query with several `domains` runs one search per domain, so one failing domain keeps the others' hits); a missing CLI stops the run with one error.
2. **Triage.** Each lead shows title, host, snippet, *why it was flagged* (matched words), first seen, and the queries that surfaced it. Actions: **Capture**, **Dismiss**, **Snooze** (3/7/30 days; it returns to *To triage* when the snooze ends), **Restore**. Dismissed leads stay dismissed when a later search sees them again.
3. **Capture.** Scrapes the page with `max_age_ms=0` into `acquisition/captures/` (one Firecrawl scrape). *Details* then shows the captured text (escaped, truncated for display), content hash and time, and **Download opportunity input template**.
4. **Hand off.** The template is a `trailforge-opportunity-input-v1` skeleton: capture path prefilled, `title`, every requirement and `kind`/`reviewed_by`/`reviewed_at` `null`, `field_evidence` empty. The unreviewed search-result title is kept only under the ignored `_lead.search_title` key (the importer ignores unknown keys); copy the real title from the capture. Add exact quotes from the capture, then use the existing `trailforge-opportunity import` flow (see [Firecrawl workspace](FIRECRAWL_WORKSPACE.md)). Nothing is auto-filled.

## Limits and cost
- One run: at most 13 catalog queries plus 1 custom query, at most 14 Firecrawl searches (a query with `domains` costs one search per domain), 10 results each, web + news. One run at a time (a second start returns 409). At most 3 captures at once.
- Custom queries: 1..200 characters and may not start with `-`. Catalog `limit` is capped at 10 per search.
- Every search and every capture spends Firecrawl credits; the full 13-query run is the expensive action. Repeat searches create new immutable artifacts under `acquisition/searches/` (unique ids, never overwritten).

## What is stored (under the experiments directory, default `.trailforge-experiments/`)
- `leads.sqlite3` - leads (id = first 16 hex of sha256 of the normalized URL; URLs are lowercased by host and stripped of fragments, `utm_*`, `gclid`, `fbclid`, trailing slash) and a table of search runs.
- `acquisition/searches/*.search.json` - raw Firecrawl search responses; `acquisition/captures/*.capture.json` and `*.acquisition.json` - captures and their provenance.

## Honesty rules
- The *RFP-like / project-like / no match* label and the matched words are a **deterministic keyword heuristic** over title, snippet and URL. They are not verification, not a deadline, not a power requirement, and not a statement that an RFP is open.
- The Find tab never infers deadlines, MW, or buyers, and shows no synthetic data. Captured text is untrusted public content; all web text is rendered as plain text, and links open in a new tab with `rel="noopener noreferrer"` only for http(s).
- Every mutation needs the session token; only the Firecrawl calls you start leave the machine. Nothing is sent to buyers, suppliers, or anyone else.
