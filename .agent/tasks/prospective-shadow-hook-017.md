# Prospective shadow hook 017

## Objective

Add a local, immutable prospective-shadow capture boundary required by the
canonical Arena packet, without adding network acquisition, outcomes, scoring,
or commercial authority.

## Allowed files

- `src/athena_procurement_arena/shadow.py`
- `src/athena_procurement_arena/__init__.py`
- `src/athena_procurement_arena/runner.py`
- `tests/procurement_arena/test_shadow.py`
- `docs/HISTORICAL_FIXTURES.md`
- `docs/PRD_ALIGNMENT.md`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `.agent/artifacts/prospective-shadow-hook-017/COMPLETION.json`
- `.agent/artifacts/prospective-shadow-hook-017/REVIEW.json`

## Requirements

- Capture only a source fingerprint, point-in-time metadata, frozen prediction,
  and replay manifest.
- Reject unknown source provenance and any embedded outcome at capture time.
- Preserve no-network and no-commercial-authority boundaries.

## Acceptance checks

- Capture is deterministic for an identical policy/scenario input except for
  explicitly supplied capture time.
- Invalid provenance and outcome-bearing capture inputs fail closed.
- Full local validation passes.

## Output artifacts

- Capture primitive, tests, documentation, completion receipt, and review receipt.

## Role budgets

- Builder: one narrow implementation pass.
- Reviewer: deterministic diff and validation review.
