# Revised packet: negative-knowledge-context-036b

Status: READY. Base: `c9a5fd7d99130aad37eab82c3a56c5dd125f12cd` on
`codex/negative-knowledge-036`. Owner: one Luna builder. Controller direction:
`REDIRECT` after packet 036's two local repairs and three `CORRECT` audits.

## Canonical intent and failure

Build Packet #0 v1.0 requires rejected lessons to persist so failed ideas are
not rediscovered repeatedly, while hard invariants and missing evidence remain
fail closed. The current snapshot/content hash and early reuse behavior are
implemented, but exact candidate `c9a5fd7` can skip a changed evaluated lesson
because the evaluation-context fingerprint omits `world.py` and
`foundation.py`. A read-only reviewer probe changed `EvidenceEvent.visible_at`
and observed different full lesson metrics with `SKIPPED` reuse.

## Objective

Replace the fragile handpicked evaluation-context source list with a
deterministic, conservative fingerprint of the complete local procurement
Arena source package plus the shared `athena_arena` source it imports, bound
to seed and registry. Any missing/unreadable source must yield an explicit
conflict, not a skip. Keep the policy/config fingerprint and typed full-lesson
hash. This may conservatively re-evaluate after an unrelated source edit; do
not weaken identity to improve reuse rate.

## Allowed files and acceptance

Own `src/athena_procurement_arena/athena_optimizer.py`, directly affected
`tests/procurement_arena/test_athena_optimizer.py`, and
`.agent/artifacts/negative-knowledge-036/COMPLETION.json`. Preserve all
`REVIEW-*.json`, canonical packet, fixtures, policy logic, promotion rules,
CI, and protected evidence.

1. Same seed and unchanged complete source surface: a loaded exact rejected
   idea skips before candidate evaluation, robustness, CandidatePolicy, and
   tournament, with visible stored-lesson digest and zero promotion.
2. Different seed, changed world/foundation source, or unreadable package
   source: visible top-level conflict, never `SKIPPED`.
3. Tests do not mutate real repository source. They prove package enumeration
   includes `world.py` and `foundation.py`, and simulate a source change in a
   temporary copy or through a bounded digest hook. Preserve other candidate
   results and no-store behavior.

## Validation and authority

Run focused tests and the complete local gate once the implementation and
completion artifact are frozen. Controller repeats the gate and commissions a
fresh independent audit on the exact local commit. No GitHub/network
validation, commit by builder, push, merge, deploy, self-promotion, or
real-world accuracy claim. Preserve others' work. Report exact commands,
exit codes, files, and UNKNOWNs.
