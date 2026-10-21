# Trailforge

Trailforge is a customer-first power-project desk for recording real project
signals, verifying temporary-power needs, mapping the sourced buyer chain, and
preparing human-led customer conversations. It keeps sources, unknowns, and
corrections visible. Drafts are never sent from the app, and fuel coordination
stays downstream of a verified need and an understood customer conversation.

The repository also contains Athena's deterministic Procurement Arena, a
separate research environment for testing evidence-trail policies. Its
historical mechanics and research gates remain independent of the operator desk.

## Build approach

Start with one small, reproducible scenario-to-outcome path. Build it, run it, observe the result, fix what fails, and ship. Add tournament or review machinery only when an explicit comparison needs it. Temporal evidence, deterministic evaluation, and the research-only boundary remain core requirements.

## Check
Optional local workbench: run `uv run --python 3.11 trailforge-ui`, then open
the printed loopback URL to choose GT-003, save, inspect and replay experiments.
Results remain UNSEALED / UNSCORED. See [local UI quickstart](docs/LOCAL_UI.md)
for Windows commands, restart recovery, installed-wheel use and boundaries.

For the customer-first local project desk, run
`uv run --python 3.11 trailforge-operator --data .trailforge-operator.sqlite3`
and open the printed loopback URL. Its first panel checks the official Microsoft
Local and QTS News feeds only when requested; review a candidate and explicitly
create its project file. Coverage is narrow, items are not automatically
qualified, and feed or excluded-link counts remain visible. It retains project evidence, buyer research,
conversation drafts and human-entered interactions locally; it does not send
messages. Fuel coordination stays locked until reviewed power-need evidence and
a conversation that records MW, timing, duration and site constraints. See
[operator quickstart](docs/OPERATOR_QUICKSTART.md).

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

Run the local scenario/replay mechanics directly from the retained GT-003
fixture bundle. Start in the project directory (or replace this path with the
checkout root on your machine); the experiment directory must be new:

```powershell
Set-Location 'C:\Users\nrsan\Nucleus\02_Projects\Trailforge'
$experimentDir = Join-Path $env:TEMP ('trailforge-gt003-' + [guid]::NewGuid().ToString('N'))
uv run --python 3.11 python -m athena_procurement_arena scenario --bundle scenarios/fixtures/verified/gt-003-morgan-hill.json --fixture-id GT-003 --experiment-dir $experimentDir
uv run --python 3.11 python -m athena_procurement_arena inspect --experiment-dir $experimentDir
uv run --python 3.11 python -m athena_procurement_arena replay --experiment-dir $experimentDir
```

The retained bundle and its selected fixture/reviewer/source context are saved
with the experiment, so later inspect and replay do not need the original
bundle path. Bundle structure validation does not authenticate reviewer claims
or historical source capture, and a saved `source_sha256` does not mean that raw
source bytes were retained. `--fixture-id` selects exactly one fixture; unknown
IDs and mixed bundle/scenario inputs fail. The evaluation remains unsealed and
unscored even when the fixture carries a stored status claim.

Older plain scenario JSON remains supported through `--scenario-file` with
`--experiment-dir`, and legacy manifest workflows remain available.

For a durable experiment directory, use `--experiment-dir` instead of the
legacy `--output` manifest path. The directory stores the original scenario
text, decision ledger and decision-time snapshots, separate unsealed evaluation,
configuration/source identity, and a hash-bound manifest. Inspect verifies the
saved artifacts and reads them without rerunning the policy; replay verifies
those hashes and then reruns the deterministic policy against the retained
input:

`inspect` prints indented JSON so the ordered decision snapshots and separate
evaluation can be read directly in a terminal or redirected to a file.

Experiment creation refuses an existing directory. Artifact hashes detect
accidental or isolated changes; they are integrity checks, not signatures
against deliberate coordinated rewriting. Ordinary JSON scenario truth remains
unsealed, so outcome metrics are unavailable and unscored.

This unsealed source-backed input demonstrates mechanics only; it does not
establish historical accuracy or scoreable evidence. The former seed-only
pseudo-replay has been intentionally removed. Use `smoke` for an explicit
synthetic mechanics run.

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
