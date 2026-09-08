# Current opportunity workflow

Trailforge separates opportunity discovery from verified current lead output.

## Qualification gates

A record reaches the current shortlist only when all gates pass:

1. The source record is locally captured and source-verified.
2. The opportunity lifecycle is `OPEN`, `ACTIVE`, or `SOURCES_SOUGHT`.
3. The source evidence identifies prime/continuous operating power.
4. Required capacity is at least 300 kW.
5. The scope includes temporary power or generator installation/replacement.

Emergency-backup-only and maintenance-only records are excluded. Maintenance that
is incidental to a qualifying installation or rental does not by itself disqualify
the record.

## Running results

```powershell
cd C:\Users\nrsan\Trailforge
$env:PYTHONPATH="src"
python -m athena_procurement_arena shortlist --bundle path\to\bundle.json
```

The output is JSON with `status`, `count`, and compact provenance-bearing
`fixtures`. A zero count means no record in that bundle passed every gate; it does
not mean the broader market has no opportunities.

## Current research checkpoint

As of 2026-09-08, the checked-in source-backed generator records are historical or
otherwise non-current. PSEG Long Island/LIPA's 2026 Temporary Generation RFP is a
promising held candidate, but its public listing does not verify a per-project
minimum capacity or prime rating. See
`research/current-opportunity-screen-2026-09-08.md` and
`.agent/artifacts/current-opportunity-screen-015/SCREEN.json`.

## Boundaries

This workflow does not perform live scraping, source verification on the user's
behalf, vendor outreach, bid preparation, response submission, award prediction,
or generator maintenance services. It preserves source URLs, retrieval times,
verification notes, and lifecycle status for human review.
