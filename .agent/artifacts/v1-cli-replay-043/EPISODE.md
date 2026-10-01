# Slice 1 checkpoint

State: clean local c216b5e; 182 tests passed; real scenario-file and saved-manifest replay inaccessible through the CLI. Remote divergence 29/1.

Decision: reuse the existing DSL/runner, one Luna implementation lane, four implementation files, no new architecture.

Action: connect input/save/replay, exclusive output creation, fail-closed status, quickstart and build-output ignores.

Outcome: initial candidate passed 185 tests, but independent Sol found non-object manifest JSON escaped as AttributeError. Preserve REVIEW-1. Repair added CLI boundary handling and four regression cases. Final 189-test gate and GT-003 separate-process/isolated-wheel replay passed; independent REVIEW-2 PASS for exact hashes.

Attribution: happy-path and syntax-error tests did not exercise valid JSON of the wrong root type. The failure came from the loader's object assumption, not from replay mechanics or environment.

Candidate lesson: when exposing an existing parser at a CLI boundary, include valid-but-wrong-shape JSON among boundary checks. Metric: four previously uncovered JSON root classes now return structured FAIL/nonzero. This is a local candidate lesson, not a global memory/config change or generalized speedup claim. Reversible via the scoped code/test diff.

Direction: stop after Slice 1; next is durable decision/evaluation output. Preserve source-identity, cancellation, real-evidence and remote-state limitations. No push, merge, deployment or deletion.
