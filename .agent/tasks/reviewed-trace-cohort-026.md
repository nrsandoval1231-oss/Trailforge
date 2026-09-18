# Reviewed trace cohort 026

## Objective

Assemble multiple reviewed project traces into a deterministic, hash-bound
manifest that can be reused by later backtests.

## Exclusions

No outcome inference, negative labeling, automatic identity resolution, Athena
optimization, crawling, outreach, or promotion authority.

## Acceptance checks

- Require at least one trace, unique project IDs, reviewer, and timestamp.
- Record each source path, project ID, and trace hash.
- Re-verify the cohort hash and every member trace hash on load.
- Provide a deterministic CLI and tests.
