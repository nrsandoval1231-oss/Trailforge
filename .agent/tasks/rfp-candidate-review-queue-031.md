# Build Packet: rfp-candidate-review-queue-031

## Objective

Add a local, hash-bound queue manifest that batches existing RFP candidate JSON
files for human review without accepting, screening, or fetching them.

## Allowed files

- `src/athena_procurement_arena/rfp_candidate_queue.py`
- `src/athena_procurement_arena/cli.py`
- `src/athena_procurement_arena/__init__.py`
- `tests/procurement_arena/test_rfp_candidate_queue.py`
- `README.md`
- `.agent/artifacts/rfp-candidate-review-queue-031/`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`

## Requirements

- Load only valid hash-bound candidate JSON through the existing loader.
- Manifest binds every candidate ID/hash, rejects duplicate IDs and overwrite,
  excludes raw excerpts, and has a stable queue hash.
- Every record remains `PENDING_REVIEW`; no lifecycle, qualification, fixture,
  shortlist, network, acceptance, outreach, Athena update, or promotion path.
- CLI `build-rfp-review-queue` emits deterministic JSON; focused/full gates and
  independent review are required.
