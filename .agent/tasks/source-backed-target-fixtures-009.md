# Source-backed target fixtures 009

## Objective

Add source-backed training fixtures focused on emergency generator installation, replacement, and temporary-power readiness.

## Allowed files

- `.agent/tasks/source-backed-target-fixtures-009.md`
- `.agent/artifacts/source-backed-target-fixtures-009/COMPLETION.json`
- `.agent/artifacts/source-backed-target-fixtures-009/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `scenarios/fixtures/verified/gt-007-pleasanton.json`
- `scenarios/fixtures/verified/gt-008-mobile.json`
- `tests/procurement_arena/test_fixtures.py`

## Requirements

- Use official City of Pleasanton and City of Mobile procurement pages.
- Include only installation, replacement, procurement, or temporary-power facts.
- Mark both fixtures `VERIFIED` but not `SEALED_READY` because award outcomes are not established by the captured pages.
- Preserve source fingerprints and point-in-time availability.
- Validate both bundles through the existing loader.

## Acceptance checks

- `python -m pytest -q`
- `python -m ruff check src\\athena_procurement_arena tests\\procurement_arena`
- Both fixtures load and classify as in-scope.
- Neither fixture is holdout-scoreable.

## Output artifacts

- Completion and reviewer JSON under `.agent/artifacts/source-backed-target-fixtures-009/`.

## Role budgets

- Builder: bounded fixture and test update.
- Reviewer: inspect source facts, diff, artifact, and validation output.
