## Problem and change

TrailForge has deterministic replay infrastructure but lacks a reusable real-case
cohort workflow. This adds a source-bound case manifest, procurement-family and
capture/scenario integrity checks, and an offline cohort command over the
existing TemporalWorld, frozen ledger and BASELINE_A experiment store.

A small PRE_RFP_BASELINE_V1 callback researches supported project-specific
generation needs with a concrete reason and an organization to investigate. It
permits unknown MW, rejects UNKNOWN placeholders, and suppresses supported
already-awarded, supply-resolved and non-generation cases. BASELINE_A is preserved.

## Real evidence and results

- Eight real development families across utility, data center, institutional,
  and fixed oil-and-gas contexts; eleven primary-source captures.
- Four observed procurement/delivered-generation outcomes, one non-generation
  consultancy negative, three unresolved cases.
- Three capture-time pre-RFP-baseline research surfaces; zero BASELINE_A surfaces.
- Eleven historical source records remain UNKNOWN for historical availability.
  Separate capture-observation records become visible only at capture time.
- Zero supported historical lead-time results, zero independent discovery
  credit, and no sealed holdout or Athena promotion.

All cases were exposed during development. These results prove acquisition,
source binding and replay mechanics, not earlier discovery or predictive success.
The corpus includes full captured RFP text and amendment text where available;
retained Firecrawl markdown is not an original PDF binary or historical archive.

## Validation

- `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`:
  318 passed, 1 Windows symlink-privilege skip; compile, Ruff and three fixture
  bundles passed.
- `uv run --python 3.11 --with pytest python -m pytest tests/procurement_arena -q -ra`:
  318 passed, 1 skipped.
- Two real-cohort replays with network connections and Firecrawl capture disabled:
  identical per-case input, experiment and decision hashes. Output directory is
  the only per-case result normalization; aggregate JSON hashes bind that directory.
- Exact candidate and controller evidence:
  `.agent/artifacts/pre-rfp-slice-a/CANDIDATE-portability.json`, `CONTROLLER_VALIDATION.json`, and `CONTROLLER_PORTABILITY.json`.
- Independent review verdict: `.agent/artifacts/pre-rfp-slice-a/REVIEW.json`.

- Packaging gate repeated successfully. Scoped Git attributes preserve hash-bound
  evidence on Windows: 213 indexed files byte-identical after fresh checkout,
  all eight cases loaded and all eight experiment bundles verified.

## Boundaries and next slice

This is the first implementation slice, not completion of the pre-RFP lab.
Historical precursor/version proof, broader relevance classifier/scanner,
20–50-case expansion, untouched holdout, equal-attention-budget comparisons,
Athena research-order experiments and prospective name-blind discovery remain
explicitly deferred. No outreach, submission, merge, deployment or GridLens
promotion is included.

Workflow: `docs/PRE_RFP_SLICE_A.md`.
Detailed validation: `docs/PRE_RFP_IMPLEMENTATION_VALIDATION_2026-10-02.md`.
