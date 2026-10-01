# Repair packet: episode-action-basis-039, attempt 1

Base: `4f1639fc64d8cc8e9f86b7953a2626e86a887ab0` on
`codex/episode-action-basis-039`. Raw Astra verdict: `CORRECT`, retained in
`.agent/artifacts/episode-action-basis-039/REVIEW-1.json`.

## Objective and ownership

One Luna builder owns `src/athena_procurement_arena/evaluation.py`,
`world.py`, directly affected `tests/procurement_arena/test_evaluation.py`,
`test_world.py`, `docs/EVALUATION.md`, and a concise repair handoff under
`.agent/artifacts/episode-action-basis-039/`. No other files.

1. Reuse the full existing explicit-discovery eligibility (all basis IDs
   nonblank strings and visible) before granting useful lead. Regression:
   `['e', None]` and `['e', 'not-visible']` must yield no lead even when `e`
   has a valid attestation. Preserve ordinary discovery contract and honest
   `None` for absent support.
2. Ensure policy state in `TemporalWorld.step` cannot expose a future-reviewed
   `action_support`: reveal its annotation only at/after `reviewed_at` while
   leaving base evidence visibility intact. Do not mutate the underlying
   scenario or reveal truth to policy. Regression with a callback inspecting
   the actual state before and after the review timestamp; preserve scenario
   hash and replay determinism.
3. Keep research-only authority, protected fixtures, canonical requirements,
   CI, and promotion gates untouched. No invented real-world outcomes.

Run focused checks, then the complete local gate on the frozen candidate.
Report exact files, commands, exit codes, and UNKNOWNs. No network/GitHub
validation, commit, push, merge, or deploy. Controller repeats the gate and
requests fresh independent audit on the exact repaired commit.
