# Procurement Arena current state

Foundation slice `procurement-arena-foundation-001` passed local validation.
The repository now has research-only typed temporal evidence, scenario
validation, conservative power-gap primitives, and an immutable frozen
decision ledger under `src/athena_procurement_arena`. The versioned scenario
DSL and deterministic temporal world engine are also implemented; the package
now reveals evidence by verified availability and freezes each policy output.

Also implemented: deterministic policy contract, controls, BASELINE_A,
component evaluator, adversarial/counterfactual helpers, Athena governance and
negative knowledge, historical registry boundaries, and run manifests. The
mechanics campaign completed 10,000 seeded runs with zero invariant failures.
The CLI now exposes all declared local mechanics modes and emits JSON output;
`compare --count 1000` and `replay --seed 21` both passed.

Next bounded slice: expand the scenario-family corpus and add tournament
minimum floors/Pareto gates; historical scoring remains blocked until fixture
availability is verified.
Piecewise power profiles now include need and supply boundaries, preserve
unknown supply, calculate gap/duration segments, and feed verified numeric
errors into the evaluator.
All 40 registered scenario families now produce validated seeded templates.
Seeded truth-preserving mutations and same-scope power-overlap protection are
implemented and tested.
Typed customer, utility, contract, research, readiness, and critical-path
contracts are implemented. Scenario DSL serialization round-trips with an
identical hash.

Next bounded slice: execute all 40 families through controls/BASELINE_A,
produce regression metrics, and tighten campaign/tournament reporting.
The 40-family regression and all 10 declared CLI modes now pass integration
checks; the full test suite is 23 passed.
Trailforge is now a local Git repository on `master`; manifests record the
source commit and the worktree is clean.
Current full suite: 30 passed.
Tenant isolation is now enforced on every scenario evidence item; synthetic
scenario factories assign matching tenant IDs and the full suite is 32 passed.

Packet-named architecture, DSL, policy, evaluation, governance, and historical documentation is present; unverified historical replay remains non-scoreable.
Evaluation now includes Precision@K/Recall@K attention metrics for K=5, 10,
25, and 50, with empty/late alerts receiving no early-credit.
Evidence provenance now includes authority, source spans, entity candidates,
permission scope, and contradiction references through the schema and DSL.
Evidence lineage deduplication and conservative identity-resolution outcomes
(`MERGE`, `PROVISIONAL`, `UNRESOLVED`, etc.) are now executable and tested.
The 100,000-run seeded campaign completed with zero invariant failures at
approximately 5,888 runs/second; this remains mechanics evidence only.
CLI adversarial mode now runs the amendment recurrence adversary, and CLI
tournament mode now runs governed promotion gates rather than placeholders.
Family regression now evaluates all 40 templates and nests a governed
tournament decision with separate policy metrics.
`verify_replay` now checks an existing manifest's scenario and result hashes
against a fresh replay.
Power profiles expose explicit segment durations, and readiness decisions now
distinguish mandatory failures from unknown blocker-resolution requirements.
Run manifests now include metrics, invariant results, and artifact paths in
addition to source/scenario/result hashes.
Manifests can now be written to and loaded from JSON files; replay verification
accepts the persisted artifact.
Trailforge is installable from `pyproject.toml`; Ruff passes on project-owned
code/tests, and the latest 100,000-run benchmark passed at approximately 6,020
runs/second with zero invariant failures.
The final current-HEAD benchmark passed at approximately 5,476 runs/second.
BASELINE_A now explicitly handles private/direct routes, extensions, rebids,
cancellations, cross-project signals, numeric power mismatch, and amendment-only
adversarial evidence without promoting it to a procurement signal.
Campaign 001 is now documented at `reports/ARENA_CAMPAIGN_001_REPORT.md` with
results, limits, bottlenecks, and next experiments.
The packet's 1,000-variant mutation campaign, five-case counterfactual suite,
and declared `unit` CLI mode are now executable and passing.
Final audit also passed all 11 CLI modes, 1,000 mutations, and 5 counterfactuals.
Direct coverage now includes state duration, split/reassign identity outcomes,
and actionable-only useful lead time; current suite is 45 passed.
Athena optimization loop 002 is now implemented. It evaluates four deterministic
candidate policies across all 40 scenario families, emits AthenaInput,
CandidateLesson, and CandidatePolicy artifacts, and routes candidates through
all six governance gates. The new local `optimize` mode passed; current suite is
47 passed. Without sealed holdout evidence, promotion count remains zero.
Athena threshold search 003 now evaluates weighted-score thresholds 2, 4, and 6
as real candidate parameters, including typed EvidenceEvent compatibility. The
search is deterministic, passed the optimize CLI, and current suite is 48
passed. No threshold was promoted; synthetic mechanics evidence remains
insufficient for a production-quality policy claim.
Verified fixture boundary 004 is now implemented. Versioned fixture bundles
require source URL, SHA-256 fingerprint, retrieval timestamp, verifier, and
verification notes; only SEALED_READY fixtures may enter a holdout. Deterministic
seeded splitting and round-trip loading pass; current suite is 52 passed. No
historical source evidence has been fabricated or marked verified.
Source-backed fixture 006 adds GT-003 for the City of Morgan Hill's 2027
Generator Maintenance Services solicitation. Its official publication, closing,
addendum, buyer, and scope facts are captured with provenance and a fingerprint.
It is VERIFIED training evidence but not SEALED_READY because the source does not
establish a completed award outcome. Current suite is 54 passed.
Temporary power scope 007 now excludes maintenance-only opportunities across all
built-in policies. Installation, replacement, rental, and temporary-power work
remain eligible when maintenance is incidental to that scope. Current suite is
55 passed.
Scope-labeled corpus 008 now carries explicit MAINTENANCE_ONLY,
TEMPORARY_POWER_OR_INSTALLATION, and UNKNOWN family labels through temporal
replay. The maintenance-only family is excluded and representative target
families remain eligible; all 40 templates validate and the suite is 56 passed.
Prime power threshold 010 now requires explicit prime power, at least 300 kW,
and temporary/install scope before any built-in policy can produce an actionable
result. Emergency-backup-only, below-threshold, non-prime, and unknown cases are
excluded or held non-actionable. Current suite is 58 passed. The first exact-fit
research match is USDA Forest Service notice 127EAU26Q0062, now historical/inactive.
Source-backed target fixtures 009 adds GT-007 Pleasanton emergency generator
replacement/installation and GT-008 Mobile emergency generator removal,
procurement, and installation. Both are VERIFIED, in scope, and non-sealed
pending verified award outcomes. Current suite is 57 passed.
Opportunity lifecycle 011 now distinguishes OPEN, ACTIVE, and SOURCES_SOUGHT
from CLOSED, AWARDED, INACTIVE, and UNKNOWN. Existing Pleasanton and Mobile
records are explicitly non-current; unknown lifecycle status fails closed. Current
suite is 59 passed.

Current target shortlist 012 now returns only current source-verified fixtures that
also meet IN_SCOPE_PRIME_POWER_300KW_PLUS. Closed, unknown, below-threshold,
backup-only, non-prime, and maintenance-only records fail closed; current suite is
60 passed.

Current shortlist CLI 013 now exposes `shortlist --bundle <path>` for local,
machine-readable results. It reuses the current-target gate and emits source URL,
retrieval time, verifier, lifecycle, and verification notes. Current suite is 61
passed; no live scraping or outreach is performed.

Current opportunity screen 014 completed on 2026-09-08 with zero promoted records.
The strongest 300 kW prime temporary-power match is inactive; other screened records
are standby/emergency or below 300 kW. The shortlist therefore remains correctly
empty pending a primary-source match.

Current opportunity screen 015 identified PSEG Long Island/LIPA's official 2026
Temporary Generation RFP as a promising current candidate with up to 400 MW across
multiple projects. It remains held because the public source does not verify the
minimum per-project kW or prime rating; it is not in the shortlist.
Verified outcome scoring 005 is now implemented. Sealed fixtures can be replayed
against exact final procurement outcomes with accuracy, prediction details, and
invariant status; unsealed holdout scoring fails closed. Athena can attach these
scores to candidate results. Current suite is 53 passed.

Repository audit 016 closed three gaps between documented policy and executable
behavior. (1) The Aura intake screen accepted equipment nameplate ratings and
multi-project program aggregates as the stated per-project requirement, so a
400 MW aggregate qualified against the 300 kW gate — exactly the case screen 015
records as held. Requirement and rating/aggregate fields are now separate; only
requirement fields satisfy the gate, and rating-only evidence returns
NEEDS_REVIEW with `CAPACITY_EVIDENCE_IS_RATING_OR_AGGREGATE_ONLY`. (2) The Ruff
gate was failing with 82 E701/E702 errors despite the documented claim that it
passed; project-owned code is now expanded and clean under a ruleset pinned in
`pyproject.toml` (E4, E7, E9, F, I, UP, B). (3) CI targeted a self-hosted Windows
runner with an absolute path to one personal machine and therefore never ran; it
now runs on hosted `ubuntu-latest`, and `scripts/validate.py` is the single
cross-platform gate that Windows, Linux, and CI all invoke.

Current suite: 69 passed. All 12 local CLI mechanics modes plus `shortlist` and
`validate-bundle` pass. No new research claims, fixtures, or verified evidence
were introduced by this audit.

Candidate capture 017 adds the missing intake path. Capturing one opportunity
previously meant hand-authoring roughly 47 lines of nested JSON — evidence
events, timeline, truth record, tenant and lineage IDs, provenance, and a
manually computed SHA-256 — which is why only three fixtures existed. The new
`capture` CLI mode builds a validated single-fixture bundle from operator-supplied
facts, fingerprints a saved source excerpt, and screens the result in one
command. Captured bundles are ordinary bundles: `validate-bundle` and `shortlist`
read them unchanged, and `current_target_fixtures` applies the same fail-closed
gate. Omitted fields are never inferred. Capture performs no network access;
discovery remains manual and out of scope. Current suite: 75 passed.

Multi-source discovery 018 adds the funnel's front end. `discovery/` sweeps
configured sources (HTML listing pages via CSS selectors, JSON APIs via dotted
paths), ranks rows by triage relevance, and emits an AWAITING_REVIEW queue.
Adding a jurisdiction is a JSON config entry rather than a parser module, and
`discover --source <id> --dry-run <saved file>` validates selectors offline
before any live request. Retrieval honors robots.txt, rate limits per host,
refuses non-HTTPS, caps response size, and caches raw bytes that `capture`
fingerprints, so provenance runs unbroken from retrieval to shortlist. One
failing source does not fail the sweep. The review queue is a distinct type from
a fixture and cannot reach the shortlist; promotion runs through `capture` and
requires a named reviewer. Both shipped configs (SAM.gov v2, an HTML template)
ship DISABLED: they were written from documented shapes and have not been
verified against a live response, which cannot be done from the build sandbox
since it reaches only package registries. Current suite: 87 passed.
