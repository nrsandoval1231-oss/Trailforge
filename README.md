# Trailforge
#
Trailforge is Athena's research-only Procurement Arena: a deterministic
environment for testing evidence-trail policies. It has no scraper, customer
outreach, bid autofill, submission, broker, or execution authority.

## Check

Install the project and its check tooling once:

`python -m pip install -e ".[dev]"`

Then run the complete gate on any platform:

`python scripts/validate.py`

It runs the test suite, source compilation, Ruff, and validation of every
checked-in fixture bundle. `powershell -ExecutionPolicy Bypass -File
scripts\validate.ps1` delegates to the same script on Windows, and the GitHub
Actions workflow runs the identical steps on a hosted `ubuntu-latest` runner,
so local and remote results agree.

To run only the tests: `python -m pytest -q` (the `src` path is configured in
`pyproject.toml`).

Run a comparison with:

`python -m athena_procurement_arena compare --count 1000 --seed 21`

Historical fixtures are deliberately `UNVERIFIED` until point-in-time
availability is independently established.

## Current opportunity shortlist

Run the local, machine-readable shortlist against a versioned fixture bundle:

`python -m athena_procurement_arena shortlist --bundle path/to/bundle.json`

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
verification. The screen enforces this in code: equipment nameplate ratings,
parent-facility capacity, and multi-project program aggregates are recorded but
never accepted as the stated per-project requirement, and evidence carrying only
those returns `CAPACITY_EVIDENCE_IS_RATING_OR_AGGREGATE_ONLY`.

## Capturing an opportunity

Screening is only half the loop; a record has to get in. `capture` turns one
manually reviewed public listing into a validated fixture bundle and screens it
immediately:

```
python -m athena_procurement_arena capture \
  --fixture-id GT-009 \
  --source-url https://example-city.gov/bids/2026-tempgen \
  --excerpt saved-excerpt.txt \
  --buyer "Example County" \
  --scope "temporary power for construction and commissioning" \
  --published-at 2026-09-02T09:00:00-05:00 \
  --retrieved-at 2026-09-14T08:00:00-05:00 \
  --verified-by nick-2026-09-14 \
  --notes "Official bid page reviewed." \
  --required-kw 750 --fuel "natural gas" \
  --out scenarios/fixtures/candidates/gt-009.json
```

`--excerpt` is a file containing the source text you actually saved; its SHA-256
becomes the record's fingerprint, so a record cannot be created without the
evidence it rests on. Capture performs no network access and infers nothing: a
field you do not pass stays absent, and the screen returns `NEEDS_REVIEW` with
the missing-evidence reason rather than a qualification. The emitted bundle is
an ordinary bundle — `validate-bundle` and `shortlist` read it unchanged.

Capture is an intake path, not a discovery feed. Finding listings is still
manual.

Validate a local fixture bundle with:

`python -m athena_procurement_arena validate-bundle --bundle path/to/bundle.json`

See the [deterministic opportunity process graphic](docs/graphics/trailforge-deterministic-opportunity-process.png)
for the complete flow.
