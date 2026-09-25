# Packet: power-profile-accounting-035

Status: READY. Base: `b35294fa60abf47b8cee01927118e4c9e5056a4e` on
`codex/power-profile-accounting-035`. Owner: one Luna builder. Next `CONTINUE`
node after accepted packet 034, targeting Build Packet #0 item 9. The Arena
remains research-only.

## Objective and governing rule

The controlling Build Packet #0 v1.0 (SHA-256
`7abb4c4aeb6ab049ea1f2f8888f76bc4f9e96daa3217797b07706bf7858236d8`)
defines `G(t)=max(0, required_load(t)-dependable_supply(t))`, requires UNKNOWN
supply to stay UNKNOWN, and prohibits overlapping-scope double count (`I-12`).
Current `calculate_power_gap` returns 6 MW for a 10 MW need with 4 MW known
dependable supply; `calculate_power_profile((need,))` returns 10 MW. Reconcile
the primitives and piecewise profile without assuming unverified supply.

## Allowed files and exclusions

Own `src/athena_procurement_arena/foundation.py` and
`src/athena_procurement_arena/evaluation.py`, directly affected
`tests/procurement_arena/test_foundation.py` and `test_evaluation.py`, and
completion artifacts under `.agent/artifacts/power-profile-accounting-035/`.
Do not edit canonical packet, policy logic, campaign fixtures, protected
historical evidence, CI, execution authority, or unrelated work.

## Acceptance

1. A known 10 MW need with 4 MW dependable supply and no external supply has
   one profile segment with 4 MW dependable supply and 6 MW gap, consistent
   with `calculate_power_gap`.
2. Phased active supply gives time-correct segments and a peak gap consistent
   with those segments. Avoid crediting future supply in earlier intervals.
3. UNKNOWN baseline or overlapping active UNKNOWN supply remains UNKNOWN;
   do not coerce to zero. Peak evaluation must not score a partially unknown
   profile as if known segments establish the true peak. Preserve existing
   partial/full/phased tests.
4. Keep same-scope overlap rejection. Do not double-count baseline and external
   supply whose provenance/independence is not established. Document the
   conservative combination rule chosen for a need or multiple scopes.
5. Add focused behavioral regressions for known baseline, phased supply,
   unknown, and overlap. Do not claim the whole packet item or real-world power
   forecast accepted based on synthetic tests alone.

## Validation and handoff

Run focused tests, then freeze the completion artifact and run
`uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`.
Controller reruns that complete local gate and commissions Astra audit on the
exact local commit. No GitHub/network validation. Do not commit, push, merge,
or deploy. Preserve others' work. Default repair budget: two materially
different attempts. Report exact changed files, commands, exit codes, and
UNKNOWNs.
