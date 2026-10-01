# Current target shortlist 012

## Objective

Expose a fail-closed shortlist of source-verified opportunities that are current,
prime-power, at least 300 kW, and within temporary-power or installation scope.

## Build now

- Add `current_target_fixtures(bundle)` returning qualified `VerifiedFixture` records.
- Export it from the package surface.
- Add a regression test covering qualified, closed, and unknown lifecycle records.

## Do not build yet

- Live source ingestion, lead outreach, submissions, or maintenance workflows.
- A new lead schema that would discard fixture provenance.

## Acceptance checks

- Current status must be `OPEN`, `ACTIVE`, or `SOURCES_SOUGHT`.
- Target classification must be `IN_SCOPE_PRIME_POWER_300KW_PLUS`.
- Existing source-backed historical records remain available for audit but do not
  appear in the current shortlist.
- `python -m pytest -q` and Ruff pass.

## Allowed files

- `.agent/tasks/current-target-shortlist-012.md`
- `.agent/artifacts/current-target-shortlist-012/COMPLETION.json`
- `.agent/artifacts/current-target-shortlist-012/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `src/athena_procurement_arena/fixtures.py`
- `src/athena_procurement_arena/__init__.py`
- `tests/procurement_arena/test_fixtures.py`

## Role budgets

- Builder: Luna, 6k tokens
- Reviewer: Terra, 2k tokens
- Architect escalation: Sol only if the contract becomes ambiguous
