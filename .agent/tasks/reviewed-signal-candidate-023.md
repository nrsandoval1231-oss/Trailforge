# Reviewed signal candidate 023

## Objective

Convert a raw public capture into a human-reviewed `ProjectSignal` only when
the reviewer supplies exact project identity, signal type, observed date,
claims, and a source quote present in the captured content.

## Allowed files

- `src/athena_procurement_arena/signal_ledger.py`
- `src/athena_procurement_arena/signal_review.py`
- `src/athena_procurement_arena/__init__.py`
- `src/athena_procurement_arena/cli.py`
- `tests/procurement_arena/test_signal_review.py`
- `docs/PROJECT_SIGNAL_TRACING.md`
- `README.md`
- `.agent/artifacts/reviewed-signal-candidate-023/COMPLETION.json`
- `.agent/artifacts/reviewed-signal-candidate-023/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`

## Exclusions

No automatic extraction, project identity inference, outcome inference,
Athena optimization, promotion, contact enrichment, or outreach.

## Acceptance checks

- Candidate creation binds to an existing capture hash and exact source quote.
- Acceptance requires a named reviewer and review timestamp.
- Accepted signals preserve capture hash, source content hash, URL, quote, and
  reviewed claims.
- Tampered captures and absent quotes fail closed.
- An explicit `review-signal` CLI mode persists a reviewed signal locally.
- Tests, Ruff, compilation, fixture validation, and diff checks pass.
