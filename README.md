# Trailforge
#
Trailforge is Athena's research-only Procurement Arena: a deterministic
environment for testing evidence-trail policies. It has no scraper, customer
outreach, bid autofill, submission, broker, or execution authority.

## Check
`uv run --python 3.11 --with pytest --with ruff python -m pytest -q`

The complete local gate is available on Windows with
`powershell -ExecutionPolicy Bypass -File scripts\validate.ps1`; it runs the
test suite, source compilation, and Ruff. GitHub Actions is configured for the
same checks, but the private repository currently has no available hosted or
self-hosted runner, so a remote run may fail before checkout.

Run a comparison with:

`uv run --python 3.11 python -m athena_procurement_arena compare --count 1000 --seed 21`

Run the required domain and invariant suite through the CLI with:

`uv run --python 3.11 --with pytest python -m athena_procurement_arena unit`

Historical fixtures are deliberately `UNVERIFIED` until point-in-time
availability is independently established.

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

Screen every record in a local bundle with explainable dispositions, provenance,
reason codes, and next actions:

`uv run --python 3.11 python -m athena_procurement_arena screen-bundle --bundle path\to\bundle.json`

This is the operator queue for a bundle: qualified records are surfaced, while
missing evidence, rejected scope, and non-current records remain visible rather
than disappearing into an empty shortlist.

See the [deterministic opportunity process graphic](docs/graphics/trailforge-deterministic-opportunity-process.png)
for the complete flow.
Seal a captured prospective shadow prediction against a verified outcome:

`uv run --python 3.11 python -m athena_procurement_arena seal-prospective --shadow path/to/shadow.json --outcome SOLICITATION_RELEASED --verified-by reviewer --output path/to/seal.json`

Evaluate a cohort of sealed outcomes with governance floors:

`uv run --python 3.11 python -m athena_procurement_arena evaluate-cohort --seals seal-1.json seal-2.json --cohort-id cohort-1 --output path/to/cohort.json`

Both commands are local, network-free, and preserve ABSENT execution authority.
