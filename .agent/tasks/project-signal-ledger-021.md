# Project signal ledger 021

## Objective

Add a deterministic, local project-signal ledger that represents the chronology
from project formation through power need and procurement. Support public and
confidential evidence as separate classes, preserve source provenance and
hashes, and identify the earliest signal without inferring missing events.

## Allowed files

- `src/athena_procurement_arena/signal_ledger.py`
- `src/athena_procurement_arena/__init__.py`
- `tests/procurement_arena/test_signal_ledger.py`
- `docs/PROJECT_SIGNAL_TRACING.md`
- `.agent/artifacts/project-signal-ledger-021/COMPLETION.json`
- `.agent/artifacts/project-signal-ledger-021/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`

## Exclusions

No crawler, network calls, Firecrawl integration, contact enrichment, outreach,
model calls, outcome inference, or promotion authority. Do not add confidential
attachments to the repository.

## Acceptance checks

- Typed signal records validate timezone, evidence class, source provenance,
  source fingerprint, reviewer, and signal type.
- Public evidence requires an HTTP(S) source URL; confidential evidence uses a
  local/source reference and remains distinct from public evidence.
- Project traces sort deterministically and expose the earliest signal.
- JSON round-trip preserves stable hashes.
- Tests, Ruff, compilation, and diff checks pass.

## Next direction

After this slice passes, add a controlled public-capture adapter that writes
immutable source captures into ignored local storage and converts extracted
claims into human-review candidates only.
