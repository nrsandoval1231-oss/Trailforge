# Trailforge
#
Trailforge is Athena's research-only Procurement Arena: a deterministic
environment for testing evidence-trail policies. It permits explicit,
reviewer-bound public capture, but has no autonomous discovery, production
scraper, customer outreach, bid autofill, submission, broker, or execution
authority.

## Build approach

Start with one small, reproducible scenario-to-outcome path. Build it, run it, observe the result, fix what fails, and ship. Add tournament or review machinery only when an explicit comparison needs it. Temporal evidence, deterministic evaluation, and the research-only boundary remain core requirements.

## Check
`uv run --python 3.11 --with pytest --with ruff python -m pytest -q`

The complete local gate is available on Windows with
`powershell -ExecutionPolicy Bypass -File scripts\validate.ps1`; it runs the
test suite, source compilation, and Ruff. GitHub Actions is configured for the
same checks. The last inspected run at an older commit was blocked before
steps started by a GitHub account payment or spending-limit annotation. The
current candidate is validated locally only. See [finish readiness](docs/FINISH_READINESS.md)
for the current evidence and acceptance boundaries.

Run a comparison with:

`uv run --python 3.11 python -m athena_procurement_arena compare --count 1000 --seed 21`

Run the required domain and invariant suite through the CLI with:

`uv run --python 3.11 --with pytest python -m athena_procurement_arena unit`

The built-in historical replay registry is `UNVERIFIED`. Checked-in
source-backed GT-003, GT-007, and GT-008 bundles are `VERIFIED`, but none is
`SEALED_READY` or part of a sealed holdout. They remain non-scoreable as
real-world forecast evidence.

## Current opportunity shortlist

Run the local, machine-readable shortlist against a versioned fixture bundle:

`uv run --python 3.11 python -m athena_procurement_arena shortlist --bundle path\to\bundle.json`

The command returns only source-verified records whose lifecycle is `OPEN`,
`ACTIVE`, or `SOURCES_SOUGHT`, with explicit planned temporary, construction,
commissioning, energization, or bridge-power scope; an explicitly captured
requirement of at least 300 kW; and captured natural-gas or propane fuel
compatibility. It rejects emergency/contingency work, permanent capacity or PPA
structures, maintenance-only work, incompatible fuel, and below-threshold work.
Missing scope, requirement, or fuel evidence stays out of the shortlist with a
machine-readable review reason. A parent facility's nameplate capacity never
substitutes for the temporary-power requirement.

The shortlist is research-only. It does not scrape live sites, infer missing
requirements, contact vendors, prepare bids, submit responses, or claim awards.
The current research screen is documented in
`research/current-opportunity-screen-2026-09-08.md`; the PSEG Long Island/LIPA
2026 Temporary Generation RFP is held pending per-project capacity and rating
verification.

Validate a local fixture bundle with:

`uv run --python 3.11 python -m athena_procurement_arena validate-bundle --bundle path\to\bundle.json`

Capture one public page locally for review:

`uv run --python 3.11 python -m athena_procurement_arena capture-public --url https://example.com/project --capture-id project-2026-09-17 --captured-by reviewer --output .firecrawl/project-2026-09-17.json`

Capture is raw evidence only. It does not infer claims, qualify projects, or
contact anyone; confidential documents must never be supplied to this command.

Create a hash-bound candidate from a locally saved public source excerpt, then
have a named reviewer accept the *same* excerpt into the existing fixture and
screening path:

`uv run --python 3.11 python -m athena_procurement_arena capture-rfp-candidate --candidate-id rfp-1 --source-url https://example.com/rfp --excerpt-file .firecrawl/rfp-1.txt --source-quote "exact quote from excerpt" --buyer "Buyer name" --scope "temporary construction power" --published-at 2026-09-01T00:00:00+00:00 --retrieved-at 2026-09-02T00:00:00+00:00 --captured-by operator --output .firecrawl/rfp-1-candidate.json`

`uv run --python 3.11 python -m athena_procurement_arena accept-rfp-candidate --candidate .firecrawl/rfp-1-candidate.json --excerpt-file .firecrawl/rfp-1.txt --fixture-id fixture-1 --reviewed-by reviewer --verification-notes "Verified against saved source." --opportunity-status OPEN --output fixtures/rfp-1.json`

Candidate JSON retains only the source fingerprint and exact quote, not the raw
excerpt. Acceptance rechecks both. It requires review notes and an explicit
non-`UNKNOWN` lifecycle; it does not infer missing capacity or fuel facts, and
the resulting fixture still has to pass the normal screen before it appears in
the shortlist.

Batch existing candidate JSON files into a local, hash-bound human-review queue:

`uv run --python 3.11 python -m athena_procurement_arena build-rfp-review-queue --candidates .firecrawl/rfp-1-candidate.json .firecrawl/rfp-2-candidate.json --queue-id queue-1 --assembled-by review-coordinator --assembled-at 2026-09-03T00:00:00+00:00 --output .firecrawl/rfp-review-queue.json`

Every queue record remains `PENDING_REVIEW` and contains only its candidate path,
ID, and hash. Queue construction does not accept, screen, shortlist, or fetch a
candidate, and it refuses to overwrite an existing output.

Convert a reviewed capture into a signal only with an exact source quote:

`uv run --python 3.11 python -m athena_procurement_arena review-signal --capture .firecrawl/capture.json --signal-id orla-feasibility-2026 --project-id south-railroad --signal-type CONSTRUCTION_APPROVED --signal-title "Construction spending approved" --observed-at 2026-01-14T00:00:00+00:00 --source-quote "exact quote from capture" --reviewed-by reviewer --output .firecrawl/signal.json`

Backtest reviewed traces against a later observed milestone:

`uv run --python 3.11 python -m athena_procurement_arena backtest-traces --traces trace-1.json trace-2.json --target-type PROCUREMENT_SIGNAL --early-types FEASIBILITY_COMPLETE POWER_REQUIREMENT --output .firecrawl/backtest.json`

`uv run --python 3.11 python -m athena_procurement_arena resolve-traces --traces alias-a.json alias-b.json --identity-reviews identity-reviews.json --output .firecrawl/resolved-traces.json`

`uv run --python 3.11 python -m athena_procurement_arena build-trace-cohort --traces trace-1.json trace-2.json --cohort-id reviewed-2026-01 --assembled-by reviewer --assembled-at 2026-09-18T12:00:00+00:00 --output .firecrawl/cohort.json`

`uv run --python 3.11 python -m athena_procurement_arena backtest-cohort --cohort .firecrawl/cohort.json --target-type PROCUREMENT_SIGNAL --early-types FEASIBILITY_COMPLETE POWER_REQUIREMENT --output .firecrawl/cohort-backtest.json`

Outcome sealing is explicit and reviewer-bound:

`uv run --python 3.11 python -m athena_procurement_arena seal-trace-outcome --trace trace.json --seal-id seal-1 --target-type PROCUREMENT_SIGNAL --outcome-state OBSERVED --target-signal-id target-1 --cutoff-at 2026-09-18T12:00:00+00:00 --source-sha256 <sha256> --source-quote "exact reviewer evidence" --reviewer-statement "Target verified." --reviewed-by reviewer --reviewed-at 2026-09-18T12:00:00+00:00 --source-url https://example.com/review --output .firecrawl/seal.json`

Evaluate a cohort-bound backtest only against its matching sealed outcome cohort:

`uv run --python 3.11 python -m athena_procurement_arena evaluate-retrospective --cohort-backtest .firecrawl/cohort-backtest.json --outcome-cohort .firecrawl/outcome-cohort.json --output .firecrawl/evaluation.json`

Screen every record in a local bundle with explainable dispositions, provenance,
reason codes, and next actions:

`uv run --python 3.11 python -m athena_procurement_arena screen-bundle --bundle path\to\bundle.json`

This is the operator queue for a bundle: qualified records are surfaced, while
missing evidence, rejected scope, and non-current records remain visible rather
than disappearing into an empty shortlist.

See the [deterministic opportunity process graphic](docs/graphics/trailforge-deterministic-opportunity-process.png)
for the complete flow.

## Historical research case

See [USACE Puerto Rico power-stabilization trace](docs/USACE_PUERTO_RICO_POWER_TRACE.md).
It is unreviewed historical research, not a current opportunity or predictive claim.
Seal a captured prospective shadow prediction against a verified outcome:

`uv run --python 3.11 python -m athena_procurement_arena seal-prospective --shadow path/to/shadow.json --outcome SOLICITATION_RELEASED --verified-by reviewer --output path/to/seal.json`

Evaluate a cohort of sealed outcomes with governance floors:

`uv run --python 3.11 python -m athena_procurement_arena evaluate-cohort --seals seal-1.json seal-2.json --cohort-id cohort-1 --output path/to/cohort.json`

Both commands are local, network-free, and preserve ABSENT execution authority.
