# Explainable bundle screen 020

## Objective

Turn the local verified fixture bundle into an operator-usable screening queue:
emit every fixture with currentness, qualification disposition, reason codes,
source provenance, and a deterministic next action. Preserve the existing
fail-closed shortlist gate and the research-only/no-network boundary.

## Allowed files

- `src/athena_procurement_arena/cli.py`
- `tests/procurement_arena/test_cli.py`
- `README.md`
- `.agent/artifacts/explainable-bundle-screen-020/COMPLETION.json`
- `.agent/artifacts/explainable-bundle-screen-020/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`

## Exclusions

No network or discovery code, no scraper, no outreach, no bid preparation,
no changes to qualification semantics, no promotion authority, and no
rewriting of existing fixture evidence.

## Acceptance checks

- Add a `screen-bundle --bundle <path>` CLI mode.
- Emit all fixtures, including held/rejected and non-current records.
- Include source URL, retrieval time, verifier, lifecycle, screen result,
  reason codes, and a deterministic next action.
- Emit summary counts by disposition and preserve machine-readable JSON.
- Existing suite, Ruff, compile, fixture validation, and diff checks pass.
- No live network access is introduced.

## Handoff artifacts

Completion and independent review JSON must record exact commands, exit codes,
changed files, and remaining evidence limits.

## Role budget

One bounded implementation lane; one repair attempt if deterministic checks fail.
