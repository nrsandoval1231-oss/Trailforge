# Packet: replay-identity-042

Status: READY. Base: `1319d32caccc678e7e15ba3047f818da50e0a957`
on `codex/replay-identity-042`. Owner: one Luna builder. Dependency: full
re-audit 040 identifies manifest reproducibility as partial; packet 041 audit
also notes a pre-existing public scenario replacement/hash-binding gap.

## Objective

Close two bounded replay identity gaps. A persisted run manifest currently
drops its stored `manifest_hash` on load, so altered JSON can be silently
rehashed. `TemporalWorld` allows its public `scenario` attribute to be
replaced after construction while continuing to expose the original
`scenario_hash`. Preserve fail-closed research replay and deterministic
behavior without claiming full reproducibility.

## Allowed files and exclusions

Own only `src/athena_procurement_arena/runner.py`, `world.py`, directly
affected `tests/procurement_arena/test_runner.py`, `test_world.py`,
`docs/EVALUATION.md`, and `.agent/artifacts/replay-identity-042/COMPLETION.json`.
Do not edit policies/evaluator/tournament/governance, fixtures, scenarios,
DSL/schema, protected evidence, canonical packet, campaign report, CI,
promotion, or execution authority.

## Acceptance

1. `load_manifest` requires the persisted manifest hash and rejects a
   missing, malformed, or mismatched hash before returning a trusted
   `RunManifest`. Tampering with fields such as config or source commit must
   fail. Preserve exact round-trip for an unmodified manifest.
2. `verify_replay` reports a failed source-commit check if the manifest's
   recorded commit differs from current local `git rev-parse HEAD`; unavailable
   Git identity cannot silently pass. Keep existing scenario/result checks.
   Do not claim this detects uncommitted source edits or proves policy/config
   equivalence; document those limits.
3. `TemporalWorld.step` compares the currently validated scenario hash with
   the constructor-bound hash before policy invocation, cursor advance, or
   ledger append. A post-construction public scenario replacement fails with a
   specific invariant error and zero policy calls/records. Existing I-08
   permission rejection remains first for non-public replacement.
4. Tests cover successful manifest round-trip, missing/malformed/tampered
   stored hashes, source commit mismatch/unavailability, public scenario
   replacement, and unchanged deterministic replay. This does not upgrade
   Build Packet #0 item 15 to complete.

## Validation and handoff

Run focused runner/world tests, freeze code/tests/docs and completion artifact,
then `uv run --python 3.11 --with pytest --with ruff python
scripts/validate.py`. Controller independently repeats the full local gate
and commissions Astra audit on the exact committed candidate. No network or
GitHub validation, commit, push, merge, or deploy. Preserve others' edits.
Repair budget: two materially different attempts. Report exact files,
commands, exit codes, and UNKNOWNs.
