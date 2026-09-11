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
`ACTIVE`, or `SOURCES_SOUGHT`, and whose evidence supports prime power of at least
300 kW within temporary-power or installation scope. Closed, unknown, standby-only,
maintenance-only, below-threshold, and non-prime records are excluded.

The shortlist is research-only. It does not scrape live sites, infer missing
requirements, contact vendors, prepare bids, submit responses, or claim awards.
The current research screen is documented in
`research/current-opportunity-screen-2026-09-08.md`; the PSEG Long Island/LIPA
2026 Temporary Generation RFP is held pending per-project capacity and rating
verification.

See the [deterministic opportunity process graphic](docs/graphics/trailforge-deterministic-opportunity-process.png)
for the complete flow.
