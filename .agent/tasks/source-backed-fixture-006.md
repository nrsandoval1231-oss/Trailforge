# Source-backed fixture 006

## Objective

Add the first source-backed historical fixture using an official public procurement page, while keeping it out of sealed holdout scoring until outcome evidence is available.

## Allowed files

- `.agent/tasks/source-backed-fixture-006.md`
- `.agent/artifacts/source-backed-fixture-006/COMPLETION.json`
- `.agent/artifacts/source-backed-fixture-006/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `scenarios/fixtures/verified/gt-003-morgan-hill.json`
- `tests/procurement_arena/test_fixtures.py`

## Requirements

- Use the official City of Morgan Hill source URL.
- Capture publication, closing, addendum, buyer, and scope facts with point-in-time availability.
- Fingerprint the captured canonical source excerpt.
- Mark the fixture `VERIFIED` but not `SEALED_READY`; do not claim award/outcome evidence that is not present.
- Validate loading through the existing fixture bundle contract.

## Acceptance checks

- `python -m pytest -q`
- `python -m ruff check src\\athena_procurement_arena tests\\procurement_arena`
- The checked-in fixture loads and is not holdout-scoreable.

## Output artifacts

- Completion and reviewer JSON under `.agent/artifacts/source-backed-fixture-006/`.

## Role budgets

- Builder: bounded fixture and test update.
- Reviewer: inspect source facts, diff, artifact, and validation output.
