# FC-050 live development evidence

UTC evidence acquisition and integration began 2026-10-01; packet creation logged 22:42:11Z. Earlier repository/planning start was not separately instrumented (UNKNOWN).

- Verified origin/main `fd772eb2475b24e65ab2221aeeaf8cfe6f1d14e3`; preserved original dirty `codex/trailforge-customer-v1` checkout. New attached worktree and branch started from origin/main.
- Firecrawl CLI authenticated and real search/scrape calls succeeded. Initial searches retained under research/firecrawl-2026-10-01/discovery-raw.
- Product adapter successfully ran official-domain then broad searches and retained LIPA landing/RFP/interconnection, county permits/parcel/agenda, Dominion utility page and corroborating local news.
- First multiple-format shell invocation failed because unquoted PowerShell comma split the format option; quoted format fixed it without changing access behavior.
- Initial product wrapper failed for public permit URL containing `&` on Windows. Builder changed invocation from .cmd to direct Node/CLI entry; real exact URL then succeeded. During live development an indentation error blocked a test run until builder compiled/repaired it; no source artifacts were created by those failed attempts.
- Initial importer run in local workspace used pre-fix freshness metadata and returned UNKNOWN/NEEDS_REVIEW. Original records retained locally under ignored workspace; sources/input v1 remain in Git evidence.
- Identical-text recapture exposed filename collision when keyed by content hash. Builder changed capture storage to full capture hash, retaining content hash separately. Input v2 uses final URL-safe permit capture and fresh LIPA landing capture. Source bytes were not overwritten.
- Parent import to workspace-v2 succeeded for both: LIPA OPEN_AS_OF_PUBLIC_SOURCE/NOT_FIT (PPA), Plaza PRE_RFP_PROJECT/NOT_SCREENED. Parent added editable 22-section draft based on RFP 5.2.2, with explicit unverified capability/pricing/portal gaps.
- Initial HTML render exposed relative links being sent to HTTP(S)-only URL validation; builder repaired local-artifact link validation. Final evidence/gates are recorded separately after freeze.

These are development observations, not acceptance. No bid, contact, merge, deployment, historical signal validation or GridLens promotion occurred.
