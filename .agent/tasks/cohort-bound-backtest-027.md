# Cohort-bound backtest 027

## Objective

Run deterministic lead-time measurement against a verified multi-project trace
cohort and bind the report to the cohort hash.

## Exclusions

No outcome inference, negative labeling, automatic identity resolution, Athena
optimization, crawling, outreach, or promotion authority.

## Acceptance checks

- Load and verify the cohort manifest and every member trace before analysis.
- Preserve the existing unresolved-case semantics.
- Emit a report containing cohort identity, cohort hash, and report hash.
- Provide a deterministic CLI, tests, full validation, and diff checks.
