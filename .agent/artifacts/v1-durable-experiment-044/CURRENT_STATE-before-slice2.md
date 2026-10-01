# Procurement Arena current state

## Current checkpoint (2026-09-25)

The entries below are chronological build notes, not a current completion
claim. Clean local `main` at the start of this checkpoint was `1319d32` after
packet 041; packet 042's exact reviewed code candidate is `7881171` and its
independent bounded verdict is `ACCEPT`. Packet 040's independent full
20-item Build Packet #0 re-audit at `32a536f` returned `CORRECT`: nine
bounded mechanisms `PROVEN`, eleven requirements `PARTIAL`. Packet 041
enforced public-only evidence permission in replay, and packet 042 checks
persisted manifest hashes, local commit identity, and scenario hash drift.
Their bounded reviews do not update the packet 040 item counts or certify the
full packet. Local validation only; sealed real outcomes, governed holdout
comparison, policy-promotion decision, and real-world accuracy remain
`UNKNOWN`. The Arena retains research-only authority.

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

Canonical PRD alignment 016 verified the authoritative Build Packet #0 retained
under Nucleus archive (SHA-256 `7abb4c4aeb6ab049ea1f2f8888f76bc4f9e96daa3217797b07706bf7858236d8`).
The mutation engine now covers deterministic availability, lineage, route,
funding, supply, demand, authority, duplication, identity, buyer, schedule, and
contradiction variants while preserving GroundTruth. The CLI `unit` mode executes
pytest and returns its real status. Campaign output now records latency, peak
Python memory, in-memory storage, model calls/cost, and failures. Current suite
is 68 passed. Historical and prospective evidence remain intentionally
non-scoreable until independently sealed; no promotion or real-world accuracy
claim is authorized.

Prospective shadow hook 017 now captures manually verified source provenance and
an immutable prediction manifest with `execution_authority = ABSENT`. Capture
rejects known outcomes and invalid fingerprints. It is not a shadow outcome
cohort, scoring path, network feed, or commercial execution path.
Prospective outcome seal 018 now binds captured shadow predictions to locally verified outcomes, producing an immutable ProspectiveOutcomeSeal with execution authority ABSENT. Seals round-trip through JSON, cohort-level evaluation applies governance floors and Pareto comparison, and the `seal-prospective` and `evaluate-cohort` CLI modes persist results locally. No network access, outcome inference, or promotion authority is introduced. Current suite is 80 passed.
Repository audit infrastructure 019 ports the remaining CI/Ruff/validation fixes from PR #1: a pinned Ruff ruleset (E4, E7, E9, F, I, UP, B) and line length in `pyproject.toml`, a cross-platform `scripts/validate.py` gate, a `scripts/validate.ps1` delegate, and a hosted `ubuntu-latest` GitHub Actions workflow. The E701/E702 compressed-statement style issues are expanded across `athena_arena.contracts` and procurement-arena domain/robustness/tests. No discovery, capture acquisition, or network code was ported. Current suite is 85 passed; the single `validate.py` gate passes on a clean checkout.

Explainable bundle screen 020 is implemented in the local CLI. `screen-bundle`
emits every fixture with lifecycle/currentness, source provenance, qualification
disposition, reason codes, and deterministic next action, plus disposition
counts. The existing shortlist gate is unchanged. The bounded repair ensured
rating/aggregate-only capacity maps to per-project-capacity verification before
the generic missing-requirement action. Current suite is 86 passed; the complete
local validation gate and all three real verified bundle smoke screens pass.
The verified bundles remain non-current or held, and no live opportunity,
accuracy, promotion, network, or execution claim is authorized.
Project signal ledger 021 is now implemented as a deterministic local chronology
for project announcements, feasibility, permitting, EPCM, construction,
power/fuel, procurement, and operating signals. Public and confidential evidence
classes require separate provenance, source hashes, and reviewers; traces sort by
observed time and exact signal ID and expose the earliest signal. Current suite is
90 passed and the complete local validation gate passes. Public capture,
identity resolution, Athena optimization, and outcome backtesting remain deferred.
Controlled public capture 022 now provides an explicit one-URL `capture-public`
mode through the Firecrawl CLI. It rejects non-public/local targets, records raw
markdown with content and capture hashes, refuses overwrite, and keeps captured
text separate from reviewed signals. A real Orla SEC release capture completed
locally with stable hashes; current suite is 94 passed and the full validation
gate passes. Automatic extraction, identity resolution, Athena optimization,
and recurring discovery remain deferred.
Reviewed signal candidate 023 now converts a raw public capture into a
`ProjectSignal` only when a named reviewer supplies exact project identity,
signal type, observed time, claims, and a quote present in the capture. The
accepted signal retains the candidate hash, source content hash, URL, and quote.
An absent quote fails closed; the Orla capture produced a reviewed signal
locally. Current suite is 97 passed and the complete validation gate passes.
Project trace backtest 024 now measures deterministic lead time from selected
reviewed signal types to an explicit target signal type. Traces without the
target or without a preceding early signal remain unresolved; they are not
false alarms. The CLI emits a stable hash-bound report, and the smoke test
produced one matched 40-day case. Current suite is 100 passed and the complete
validation gate passes. Identity resolution, sealed negative/outcome cohorts,
and Athena optimization remain deferred.
Project identity review 025 now provides a reviewer-controlled `resolve-traces`
boundary. Explicit evidence-bound identity reviews can merge aliases into a
canonical project, preserve the review hash on re-keyed signals, and fail closed
on conflicting reviews or missing public provenance. Current suite is 103 passed
and the complete validation gate passes. Automatic entity resolution, sealed
negative/outcome cohorts, and Athena optimization remain deferred.
Reviewed trace cohort 026 now assembles multiple reviewed traces into a local
hash-bound manifest with unique project IDs and member-hash revalidation. The
CLI smoke test produced a two-project cohort; current suite is 106 passed and
the complete validation gate passes. The cohort is a research container only;
outcome labels, automatic identity resolution, and Athena optimization remain
deferred.
Cohort-bound backtest 027 now loads and verifies a trace cohort before running
lead-time measurement, and binds the result to both the cohort hash and report
hash. The CLI smoke test produced one matched case at 100% coverage; current
suite is 107 passed and the complete validation gate passes. Sealed positive
and negative outcomes are still required before Athena learning.
Retrospective outcome seal 028 now supports explicit `OBSERVED`,
`NOT_OBSERVED_BY_CUTOFF`, and `INCONCLUSIVE` states with reviewer statements,
exact evidence quotes, timestamps, and trace-hash binding. Outcome cohorts are
bound to the reviewed trace-cohort hash and expose deterministic state counts;
the CLI smoke test produced one observed seal. Current suite is 110 passed and
the complete validation gate passes. No Athena update or predictive claim is
authorized.
Retrospective cohort evaluation 029 now preserves one hash-bound case per trace
and compares cutoff-valid early-signal alerts with explicit sealed outcomes.
Matching cohort, target-type, and per-project trace hashes are mandatory;
inconclusive outcomes and unsealed projects remain visible but unscored. An
independent audit found and then verified the repair for post-cutoff alerts.
Current suite is 114 passed and the complete validation gate passes. The
one-case smoke evaluation is mechanics proof only, not predictive evidence.

Manual RFP candidate capture 030 now converts a locally saved source excerpt
into a hash-bound candidate without retaining the raw excerpt in candidate JSON.
Only a named nonblank reviewer can accept the same hash-matching excerpt, exact
quote, review notes, and explicit non-UNKNOWN lifecycle into a standard verified
fixture bundle. The ordinary existing screen remains the only path to a shortlist.
Current suite is 118 passed and the complete local validation gate passes. This
is a local reviewed intake boundary only: no acquisition, automatic acceptance,
outreach, pricing, submission, Athena update, or promotion is authorized.

RFP candidate review queue 031 batches valid hash-bound candidate JSON files
into a deterministic local PENDING_REVIEW manifest. Queue records retain only
candidate ID, candidate hash, and source path; they are frozen and revalidated
before serialization, rejecting raw excerpts, quotes, altered state, duplicates,
naive timestamps, and overwrite. Current suite is 124 passed. The queue cannot
accept, qualify, shortlist, fetch, contact, or promote a candidate.
