# Controller acceptance checklist — LOCAL-UI-047

Status: planned checks, not evidence of success. Candidate must be frozen before results and independent review.

## Repository and engine

- Full existing gate: `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`.
- `git diff --check`; confirm no engine, fixture, source attestation, or policy changes.
- Hash every changed implementation/test/doc file at candidate freeze. Bind independent review to that exact file set/base, including previously untracked files.

## Real browser path

- Start documented loopback launcher; no external services/assets. Load actual page.
- Case selection displays actual source/reviewer context and GT-003 maintenance/negative-case caveat.
- Run action creates real saved artifacts; UI shows run identity and UNSEALED/UNSCORED.
- Inspect actual decision times, actions/rationale, available evidence and ledger status.
- Explicit replay shows engine checks; artifact integrity must not masquerade as completed replay.
- Refresh and restart recover saved run, no original source required for saved inspect/replay.
- Corrupt a disposable COPY of a run: failed verification visible; no overwriting or healing evidence.
- Keyboard focus, narrow layout and safe retained-text rendering; inspect screenshot and DOM.

## HTTP and filesystem boundary

- Foreign/ambiguous Host, foreign/null Origin, missing/invalid token, malformed/oversized body, unsupported content type, unknown fields and traversal refused.
- GET cannot create or replay. Only configured cases and generated safe run IDs accepted.
- Filesystem operations stay under trusted configured experiment root; symlinks/path escape rejected.
- Listing/inspection with world/policy disabled still work. Corrupt/partial runs remain explicit failures.

## Package and handoff

- Build wheel into ignored evidence directory. Confirm bundled assets and optional console entry point included.
- Launch isolated installed wheel with explicit bundle and disposable experiments root; prove run/inspect/replay and startup from unrelated cwd.
- Document accurate Windows quickstart, trusted-local-only boundary and remaining limitations.
- Independent Sol review on frozen hashes; repairs return to Astra, maximum two distinct attempts.
- No commit, push, merge, deployment, source promotion, or full-product completion claim.
