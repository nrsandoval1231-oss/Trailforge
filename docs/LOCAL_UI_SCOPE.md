# Local experiment workbench — owner-authorized extension

On 2026-10-01 the owner approved the proposed local choose → run → inspect → replay UI and explicitly selected Astra as builder. This narrowly supersedes the earlier no-UI exclusion for this optional local adapter only. It does not change Build Packet #0 acceptance, evidence requirements, policy semantics, or research-only authority.

## One-time opening Tribunal

- Luna / Simplifier: one case picker, explicit run action, persisted results and replay; no new engine, database, accounts or background job system.
- Terra / Engineer: loopback Python stdlib server, bundled vanilla assets, configured case aliases, opaque run IDs, safe text rendering, host/origin/token checks and runtime/security tests.
- Sol / controller decision: PROCEED. Use read-only GET for discovery/inspection and protected POST for run/replay (correcting the Engineer's GET-only suggestion). Bind only 127.0.0.1. Serialize engine operations. No arbitrary browser filesystem access.

Objective: make the accepted deterministic experiment path usable without assembling shell commands.
Build now: configured local fixture selection, source/status inspection, save new experiment, list prior runs, inspect decision timeline/rationale/ledger, explicit replay verification, clear failures.
Do not build yet: case authoring/review/sealing, South Valley admission, scraping, uploads, arbitrary paths, cloud hosting, accounts, external execution, optimization or promotion.
Architecture: optional Python adapter and packaged HTML/CSS/JS, reusing existing fixture parsing and experiment engine. No third-party runtime dependency required. BASELINE_A and fixture seed are displayed as fixed supported settings, not invented controls.
Assumptions: owner launches a trusted local process and supplies trusted local bundle/root paths at startup; browser requests are untrusted. Same-user filesystem tampering is detected by existing verification, not prevented by this UI.
Major risks: localhost CSRF/rebinding, path escape, misleading evidence labels, unsafe retained-text rendering, server restart/replay incompatibility, packaged asset omission.
Sequence: bounded Astra build → controller full gates/runtime/browser/package proof → independent Sol review → bounded repairs if required → local handoff. No push/merge/deploy authorized by this request.

## Finish contract for this extension

From the documented Windows command, open the local workbench, select GT-003 (maintenance negative mechanics case), view retained source/reviewer context, run and save, inspect real decisions with time and rationale, restart server and recover saved run, verify replay, and visibly reject a corrupted run. UNSEALED/UNSCORED and missing approvals remain prominent. No artifact existence alone implies verification or prediction quality. Existing CLI behavior and fixtures remain unchanged. Full repository gates, packaged static assets, boundary tests and independent exact-candidate review must pass. Full Slice 3/V1/Build Packet #0 remain separate and incomplete.

## Design direction

An instrument workbench for a research operator: case/run rail, working result pane, and a decision-time evidence strip as the signature element. Palette: cloud #F4F7FA, ink #182B40, slate #54677B, signal blue #245DB0, evidence teal #087F83, caution amber #99610A. Display: Bahnschrift with local system fallbacks; body: Segoe UI/system sans; hashes/data: Cascadia Mono/Consolas. No font downloads. The evidence strip must encode actual retained decision times, not decorative progress or invented confidence. Keep status prose legible, keyboard navigation clear, reduced motion supported, and narrow layouts usable. This workbench structure was chosen over generic summary tiles because the user's task is inspecting a reproducible run, not monitoring commercial performance.
