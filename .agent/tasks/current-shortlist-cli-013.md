# Current shortlist CLI 013

## Objective

Make the validated current-target shortlist runnable as a local, machine-readable
result from a fixture bundle.

## Build now

- Add `trailforge shortlist --bundle <path>`.
- Load the versioned bundle, apply the current 300 kW prime-power shortlist gate,
  and emit compact records retaining fixture and source provenance.
- Add CLI regression coverage.

## Do not build yet

- Live web scraping, authentication, outreach, submissions, or award claims.
- Automatic source verification or lifecycle inference.

## Acceptance checks

- Command returns JSON with `status`, `count`, and `fixtures`.
- Only `current_target_fixtures` results are emitted.
- Source URL, retrieval time, verifier, and lifecycle status remain visible.
- Full pytest and Ruff pass.

## Allowed files

- `.agent/tasks/current-shortlist-cli-013.md`
- `.agent/artifacts/current-shortlist-cli-013/COMPLETION.json`
- `.agent/artifacts/current-shortlist-cli-013/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `src/athena_procurement_arena/cli.py`
- `tests/procurement_arena/test_cli.py`

## Role budgets

- Builder: Luna, 5k tokens
- Reviewer: Terra, 2k tokens
- Architect escalation: Sol only if the command boundary becomes ambiguous
