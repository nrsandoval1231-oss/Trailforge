# Verified fixture boundary 004

## Objective

Create a strict local fixture-bundle contract and deterministic train/holdout splitter for future source-backed Athena evaluation.

## Allowed files

- `.agent/tasks/verified-fixture-boundary-004.md`
- `.agent/artifacts/verified-fixture-boundary-004/COMPLETION.json`
- `.agent/artifacts/verified-fixture-boundary-004/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `src/athena_procurement_arena/fixtures.py`
- `src/athena_procurement_arena/__init__.py`
- `tests/procurement_arena/test_fixtures.py`

## Requirements

- Require versioned bundle metadata, source provenance, verification identity, and SHA-256 evidence fingerprints.
- Permit only `VERIFIED` or `SEALED_READY` scoreable fixture statuses.
- Preserve the existing Scenario DSL and temporal availability rules.
- Provide deterministic seeded train/holdout splitting without network access.
- Never imply that a fixture is real or scoreable merely because it parses.

## Acceptance checks

- `python -m pytest -q`
- `python -m ruff check src\\athena_procurement_arena tests\\procurement_arena`
- Valid bundles round-trip and split deterministically.
- Missing provenance, invalid hashes, and unverified fixtures fail closed.

## Output artifacts

- Completion and reviewer JSON under `.agent/artifacts/verified-fixture-boundary-004/`.

## Role budgets

- Builder: bounded implementation and tests.
- Reviewer: inspect diff, artifacts, and validation output.
