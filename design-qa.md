# Mining product design QA — 2026-10-16

final result: blocked

## Follow-up validation (isolated Windows checkout)

PR20 head `cc9c079` was reconciled with main `5eb1838` through a clean merge
(`9989ff0`). Main's phase/use-case conflict fixes are preserved. Independent Sol
source review found one overstatement: the dashboard called recorded OPEN statuses
"confirmed" even when the claim basis was OBSERVED. The label now reads
"Open package statuses in imported records"; classification logic is unchanged.

The complete gate on the integrated source passed: 475 Python tests, one existing
Windows symlink skip, source compilation, Ruff and three fixture validations.
Three Node model regressions also passed. A synthetic-only engine snapshot built,
and loopback HTTP checks returned 200 for root, JS/CSS, font/artwork, assessments,
frozen `/api/mining`, report index and `/mining/0/`. HTTP checks do not exercise
browser interactions, downloads, layout, keyboard focus or console behavior.

The supported browser failed at initialization twice (including a fresh reset):
`failed to prepare MXC sandbox: MXC requires nonempty Unicode host SystemDrive`.
No browser-policy workaround or alternate browser driver was used. Therefore no
new rendered desktop/phone acceptance or screenshot is claimed.

The approved board was resolved in Library as
`libfile_d382c95194b48191bc664e66eefa7a47` (1536 x 1024). Library read returned
an image pointer and OCR, not inspectable pixels. The current download helper
reported unavailable materialization; one explicit local-destination transfer
then failed because its mandatory metadata helper uses `os.setxattr`, unavailable
on this Windows Python. No helper was patched and no pixel comparison is claimed.
The eight original real-project manifests/captures remain unrecovered.

A separate owner-private Sites destination was registered as
`appgprj_6ad2913ac28c8191832cf81b676c835c`. Native packaging failed because its
Bash script was invoked with a Windows path. Deployment status and any transfer
artifact are recorded separately; registration alone is not a working preview.

## Source and implementation

Visual source: approved `TrailForge Industrial Intelligence Board.png` (1536 × 1024), recovered and opened from the owner's artifacts. A composite concept board, not a pixel-exact single-screen specification. Product documentation records the palette, typography and asset authority.

Implementation: existing Python application's product assets and read-only mining API; interactive snapshot at the preview host. Initial desktop browser screenshot was inspected at 1350 × 926 CSS pixels. The dashboard, Explorer, Stibnite dossier, imported synthetic multi-phase dossier and supplier matching were exercised through the cloud browser. No claim of final screenshot equivalence is made.

## Observed checks

- Dashboard navigation opens Explorer; searching Stibnite reduces six displayed records to one.
- Project selection switches from the secondary Stibnite assessment to the actual imported synthetic demonstrator.
- Early-works diesel-only scope shows DO NOT PURSUE / fuel INCOMPATIBLE for 2G.
- Switching to propane commissioning shows RESEARCH REQUIRED, POTENTIAL fuel, explicitly OPEN procurement and engineering compliance NOT ESTABLISHED.
- Dossier retains phase-specific kW, unknown peak demand, provenance, exact quotes, clocks, hashes, dependency hypotheses/falsifiers and unconfirmed commercial boundaries.
- The five real-project summaries are SECONDARY RESEARCH with dated source links, not reconstructed primary evidence.
- Console inspection showed browser-extension metadata errors; no application-origin JS error appeared in the observed states. Final-source console check is outstanding.

## Comparison and iteration

Initial implementation was compared visually with the opened board: limestone workspace, dark navigation, forest buttons, brass/copper accents and restrained density matched the direction. P2 differences: missing mountain identity, decorative mountain imagery and actual Inter font. Those have been addressed in source with a transparent mark derived from the board, generated decorative landscape, and locally bundled licensed Inter. No synthetic score gauges or illustrative mockup totals were transferred into commercial data.

**Final visual comparison remains blocked:** after preview restart the cloud browser returned ERR_BLOCKED_BY_CLIENT, followed by an explicit URL-policy rejection. No alternate browser surface or policy workaround was used. The final rendered source could not be inspected. A side-by-side final comparison, focused logo/type comparison, mobile viewport captures, final overflow/focus checks and final screenshot persistence are therefore outstanding. Earlier screenshot observations were tool-visible only; no durable final screenshot artifact exists.

## Required fidelity surfaces

- Typography: final code embeds Inter variable font; its final rendering still requires inspection.
- Spacing/layout: initial desktop rhythm inspected; final desktop and 390-pixel mobile rendering still require inspection.
- Colors: exact approved five tokens in CSS; semantic claims use visible textual badges as well as color.
- Imagery: decorative generated panorama is not a project photo; transparent raster mountain derivative is documented, not claimed as an exact approved vector master. Legacy locked brand kit retained.
- Copy: source-backed summaries and engine verdicts replace illustrative metrics; unknowns, conflicts, estimates and supplier limitations remain explicit.

## Blocking checklist

- Reopen final preview in an allowed browser session.
- Capture desktop and 390-pixel mobile views; compare with the approved board at layout/identity level, acknowledging different real content and viewport.
- Check all four views, empty results, keyboard focus, deep-link refresh, evidence disclosures, JSON download and printable report navigation.
- Inspect final console, document remaining P3 refinements, then change this report to passed only if no P0/P1/P2 issues remain.

## Independent source review

A separate reviewer found cross-phase filter mixing, stale deep-link phase indices, and an optional-method/null-range rendering crash. All three were repaired and source re-reviewed; no further important integration issues were identified. Three dependency-free Node regression tests cover these cases. This source review does not substitute for the blocked final browser/mobile acceptance.
