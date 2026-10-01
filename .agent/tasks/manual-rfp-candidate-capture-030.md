# Build Packet: manual-rfp-candidate-capture-030

## Objective

Rebuild the useful manual RFP capture concept from PR #1 as a local, hash-bound
candidate workflow. A source excerpt may create a candidate, but only a named
reviewer may accept a matching excerpt into an ordinary verified fixture bundle.

## Allowed files

- `src/athena_procurement_arena/rfp_candidate_capture.py`
- `src/athena_procurement_arena/__init__.py`
- `src/athena_procurement_arena/cli.py`
- `tests/procurement_arena/test_rfp_candidate_capture.py`
- `README.md`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `.agent/artifacts/manual-rfp-candidate-capture-030/`

## Explicit exclusions

No automatic discovery, network fetching, scraping, outreach, bid submission,
pricing, auto-promotion, Athena update, outcome scoring, or use of confidential
user material.

## Acceptance criteria

1. Candidate creation reads a local UTF-8 excerpt, requires an exact source
   quote, and records a content SHA-256 plus a stable candidate hash.
2. Candidate JSON contains no raw source excerpt. Acceptance requires the local
   excerpt again and verifies both its hash and exact quote.
3. Acceptance requires a named reviewer, non-empty verification notes, and an
   explicit non-UNKNOWN opportunity lifecycle.
4. Accepted output is a standard `FixtureBundle` using existing screening and
   shortlist gates. Candidate capture alone cannot create a fixture or enter a
   shortlist.
5. Candidate and fixture outputs refuse overwrite; all timestamps are
   timezone-aware; no input value is inferred.
6. Focused tests, full validation gate, CLI smoke tests, and `git diff --check`
   pass.

## Handoff

Write completion and independent-review artifacts under the named artifact
directory. Record exact commands, exit codes, and boundaries.
