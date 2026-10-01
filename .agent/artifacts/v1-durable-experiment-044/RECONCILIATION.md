# Phase 0 evidence

Slice 1's four implementation-file SHA-256 values matched its independent REVIEW.json before mutation. `git diff --check` passed. All uncommitted paths belonged to the accepted Slice 1 implementation and its audit/handoff artifacts.

Checkpoint: `6bde287`, message `feat: complete TrailForge V1 CLI save and replay slice`.

Fresh fetch found remote main `cb0b2419f9e2c627d0df2b180a28d868f12ae014`, one remote-only commit: `Remove finished agent packets and correct stale docs. (#2)`. Its patch changes only docs and removes historical `.agent` records. It does not change src/tests/packaging.

Reconciliation: non-fast-forward merge into feature branch only, resulting in `15247421e00303e36436961a91096efa55194ade`. Both accepted local history and remote main are ancestors. No reset, force push, branch deletion or main merge.

Resolution:

- Preserve all `.agent` evidence and state from the checkpoint, including remote-requested deletions, as explicitly required by the owner continuation brief.
- Preserve accepted README quickstart and accurate dated CI limitations; remote claims of a latest run were stale.
- Combine callable-policy architecture correction with local minimal-core direction.
- Preserve later finish-readiness hardening history and add current audit CI uncertainty.
- Correct the remote negative-knowledge claim: local history already implements hash-checked save/load.
- Retain other useful remote doc corrections and historical-report qualification.

Validation before integration commit: `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`, exit 0, 189 tests, source compilation, Ruff and three fixture validations PASS; `git diff --cached --check` PASS. `git diff 6bde287 HEAD -- src tests pyproject.toml README.md .gitignore` empty after merge. `git merge-base --is-ancestor origin/main HEAD` exit 0. Working tree clean before Slice 2 packet creation. Main unchanged at c216b5e.

The current Slice 2 packet/graph are new authorized work; historical Slice 1 reviews remain unchanged and are not retroactively extended to new implementation.
