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

## How ranking works (classifier v2)
Every lead gets a **kind** (*RFP-like*, *project-like*, or *Other*) and an integer **rank score**. Lists show the highest score first, ties broken by most recently seen. Both come from a deterministic keyword heuristic over the title, snippet and URL (`lead_classifier.py`); the card shows the matched words so you can see why.

**Kind rules**
- *RFP-like* needs an RFP word (rfp, request for proposals/qualifications/quotation/information, rfq, rfi, solicitation, ifb, tender, bid notice, "soliciting/seeking proposals or bids", sealed bids, "proposals will be opened", temporary power/generation near "procurement") or a procurement-portal host **and** energy context: a power word (temporary power, bridge power, temporary generation, generator, MW/GW, substation, turbine, interconnection, behind-the-meter, ...), a broader energy word (power, electric, energy, utility, grid, ...; "generation" and "capacity" only next to a power word), or an energy/utility host. On an official host an *addendum* or a */bids/* page also counts as an RFP word. A bare "RFP" or "solicitation" with no energy context is **Other** (card reason: *RFP wording but no energy or power context*). A procurement-portal host alone stays RFP-like but ranks lower and the card carries a *Caution* chip saying there is no energy context. The word `load` alone does not count as power relevance; "GW" counts only after a number.
- *Project-like* needs a project word that names energy infrastructure (data center, substation, compressor station, pipeline, refinery, hyperscale), or a generic one (announced, planned, construction, expansion, rezoning, ...) together with energy context. "Permit/permitting" alone never makes a project.
- **Explainer-like** hits are demoted to Other and shown with a dashed chip naming the pattern (for example `explainer-like: guide`): glossary, what is, how to, guide, understanding, best practices, market size/share/trends/forecast, study, white paper, template, FAQ, key parts, benefits/risks, overview, strategy, turnkey/solutions/services wording, policy words (bill, reform, senate), and reference hosts (Wikipedia, market-research sites). An RFP-like hit escapes the demotion when it has a strong signal: a procurement-portal host, an official host together with an RFP word, a date near deadline wording, or "request for proposal(s)" together with a power word. A project-like hit escapes only when the snippet states a size (MW/GW).
- **Other** cards say why they are there (no RFP or project words, no energy context, permit wording only, explainer-like).

**Score (a weighted sum, for ordering only)**: strong power words (temporary power/generation, bridge power, generator, MW/GW) +10 each, medium (substation, turbine, interconnection, behind-the-meter, ...) +4 each, up to four words; a strong power word in the title +6, +8 more when the title also has an RFP word; RFP word +6 (+2 for "request for proposal(s)"); procurement-portal host +8 (-12 when the snippet has no energy context); official host +8 for RFP-like, +2 for project-like (official = `.gov`/`.mil`/`.gov.xx`/`.xx.us` style hosts, not look-alikes such as `x.gov.example.com`; a small built-in list of utilities and community-power buyers, and every `domains` host of the discovery catalog in use); date near deadline wording +8; early-stage wording (announced, planned) +4, a named "Project X" +6, an event verb in the title +4; explainer-like -10; `.edu` host -4; social host (Facebook, Reddit, YouTube, LinkedIn) -8.

**Chips**
- *Rank score N* - the number above. A heuristic ordering, not a rating of how good a lead is.
- *Unreviewed* / *Heuristic: RFP-like words | project-like words | not RFP-like or project-like* - word-match results only.
- *Explainer-like: ...* (dashed) - the patterns that made the page look like a guide, report or reference.
- *Date in snippet after "due": 2026-10-30 (unverified)* or *Date in snippet after "due" is in the past: ... (unverified)* (dashed) - a date that appeared in the search snippet right after wording such as due, deadline, submit(ted) by or closing (not "due to ..." or "submitted comments on ..."). The chip names the matched word and the hover text shows the exact words. The past/future comparison is made when you load the list, against your local date, and is not stored.
- *Caution: ...* (dashed) - shown on an RFP-like or project-like card when the match is weak, for example a procurement-portal host with no energy context in the snippet. It is a quote from a search snippet: it says nothing about whether the solicitation is open, closed, extended, awarded or still current.

**Re-ranking existing leads.** The classifier has a version (`CLASSIFIER_VERSION`, also keyed on the catalog's `domains` hosts) kept in a `meta` table of `leads.sqlite3`. When it differs from the stored one, the store re-runs the classifier over all stored leads from their saved title, snippet and URL in one transaction and rewrites only `kind`, `matched` and `score`. Status, snooze, capture references and first/last seen are never touched, so dismissed, snoozed and captured leads keep their state. It runs once per version and is safe to repeat.

## Honesty rules
- The *RFP-like / project-like / Other* label, the rank score, the explainer chips and the matched words are a **deterministic keyword heuristic** over title, snippet and URL. They are not verification, not a deadline, not a power requirement, and not a statement that an RFP is open. The heuristic will demote some real leads and keep some noise; the card always shows the words it used, and Other stays one click away.
- The Find tab never infers deadlines, MW, or buyers: a date chip only quotes a date found in the snippet next to deadline wording, labelled unverified. It shows no synthetic data. Captured text is untrusted public content; all web text is rendered as plain text, and links open in a new tab with `rel="noopener noreferrer"` only for http(s).
- Every mutation needs the session token; only the Firecrawl calls you start leave the machine. Nothing is sent to buyers, suppliers, or anyone else.
