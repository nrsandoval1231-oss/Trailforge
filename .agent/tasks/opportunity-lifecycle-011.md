# Opportunity lifecycle 011

## Objective

Make source-backed fixture records lifecycle-aware so qualified prime-power projects are separated from current opportunities.

## Allowed files

- `.agent/tasks/opportunity-lifecycle-011.md`
- `.agent/artifacts/opportunity-lifecycle-011/COMPLETION.json`
- `.agent/artifacts/opportunity-lifecycle-011/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `src/athena_procurement_arena/fixtures.py`
- `tests/procurement_arena/test_fixtures.py`
- `scenarios/fixtures/verified/gt-007-pleasanton.json`
- `scenarios/fixtures/verified/gt-008-mobile.json`

## Requirements

- Add explicit opportunity lifecycle status to verified fixtures.
- Define current statuses separately from closed, awarded, inactive, and unknown.
- Preserve prime-power and scope qualification as a separate gate.
- Mark existing historical source-backed target fixtures as closed/inactive where supported.
- Do not present stale opportunities as current leads.

## Acceptance checks

- `python -m pytest -q`
- `python -m ruff check src\\athena_procurement_arena tests\\procurement_arena`
- Lifecycle status round-trips.
- Closed/inactive records are not current.
- Unknown status fails closed for current-lead selection.

## Output artifacts

- Completion and reviewer JSON under `.agent/artifacts/opportunity-lifecycle-011/`.

## Role budgets

- Builder: bounded fixture contract and tests.
- Reviewer: inspect diff, artifact, and validation output.
