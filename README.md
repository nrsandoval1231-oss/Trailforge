# Trailforge
#
Trailforge is Athena's research-only Procurement Arena: a deterministic
environment for testing evidence-trail policies. It has no scraper, customer
outreach, bid autofill, submission, broker, or execution authority.

## Check
`$env:PYTHONPATH="src"; python -m pytest -q`

The complete local gate is available on Windows with
`powershell -ExecutionPolicy Bypass -File scripts\validate.ps1`; it runs the
test suite, source compilation, and Ruff. GitHub Actions is configured for the
same checks, but the private repository currently has no available hosted or
self-hosted runner, so a remote run may fail before checkout.

Run a comparison with:

`$env:PYTHONPATH="src"; python -m athena_procurement_arena compare --count 1000 --seed 21`

Historical fixtures are deliberately `UNVERIFIED` until point-in-time
availability is independently established.

## Current opportunity shortlist

Run the local, machine-readable shortlist against a versioned fixture bundle:

`$env:PYTHONPATH="src"; python -m athena_procurement_arena shortlist --bundle path\to\bundle.json`

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

`$env:PYTHONPATH="src"; python -m athena_procurement_arena validate-bundle --bundle path\to\bundle.json`

See the [deterministic opportunity process graphic](docs/graphics/trailforge-deterministic-opportunity-process.png)
for the complete flow.
