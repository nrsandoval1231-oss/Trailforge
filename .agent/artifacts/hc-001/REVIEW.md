# HC-001 independent pilot review — FIX

Candidate: staged tree `1b7db51e440b8530cb48c674280799c6d944f025`, branch `codex/trailforge-firecrawl-vertical-slice`, base `c802a18f838c21e92dc78a354a977d2c3cf9149c`. This review concerns the bounded five-project pilot, not a completed historical lead-time measurement or product finish claim.

## Blocking finding

`historical_cohort.py:62-106` accepts an `ARCHIVED_CONTENT` or `OFFICIAL_PUBLICATION_TIMESTAMP` availability time when its URL/text binding matches, without checking that the claimed time is at or before either the cited source capture or the archive/official witness capture's own `captured_at`. An old capture containing a later scheduled timestamp, or a future-dated archive URL/text, can therefore create a `SUPPORTED` signal before the evidence could exist. The same `_availability` path is used for buyer-path proof at lines 248-259. This violates the packet's fail-closed future-timestamp requirement and can contaminate replay eligibility. Bound the asserted availability by both captures' times, reject an impossible future witness, and add focused archive, official-timestamp, and buyer regressions. Keep existing retained historical evidence unchanged.

## Evidence reviewed and limits

The retained input has five distinct real cases and ten cited signals. Literal excerpts and capture hashes are checked. The xAI archive URL, timestamp, and announcement excerpt agree; that establishes content by January 29, 2025, while the selected power-use target is reported in August 2024 and has no supported historical availability. The output correctly has one eligible early trace, zero supported targets, zero strict pairs, and UNKNOWN validated lead time. Crusoe's backup statement is not represented as a rental requirement or a site-specific portfolio order; Azure's target is undated; Montauk and East Hampton document dates remain diagnostic; buyer organizations are identified without asserting buyer-path availability. The report clearly labels its source-date intervals as diagnostic and does not claim predictive quality.

The controller's final log reports 325 tests passed, one skipped, compilation, Ruff, and three bundle checks passing. `RUNTIME-PROOF.json` records byte-identical outputs from two runs. I independently ran `git diff --cached --check`; it exited 0. I did not rerun the full suite. These gates do not cover the future-evidence case above. Repair that guard, freeze a new candidate, repeat the required gates and runtime proof, then request fresh independent review.
