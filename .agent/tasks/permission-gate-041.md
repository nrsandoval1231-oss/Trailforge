# Packet: permission-gate-041

Status: READY. Base: `da1138b321ce8d54043f810027c15d3047e64e1b`
on `codex/permission-gate-041`. Owner: one Luna builder. Dependency: full
20-item re-audit 040 returned raw `CORRECT` at `32a536f`, identifying I-08
permission exposure as a bounded, unblocked gap.

## Objective and authority

Fail closed before `TemporalWorld` exposes evidence to a policy when its
`permission_scope` has no explicit grant. The current Arena has no tenant grant
service or owner-approved non-public scope. `PUBLIC` is the only runnable
scope. Tenant matching does not imply permission. Preserve the research-only
authority boundary; this packet does not authorize confidential source access.

## Allowed files and exclusions

Own only `src/athena_procurement_arena/foundation.py`, `world.py`, directly
affected `tests/procurement_arena/test_foundation.py`, `test_world.py`,
`docs/SCENARIO_DSL.md`, `docs/ARENA_ARCHITECTURE.md`, and
`.agent/artifacts/permission-gate-041/COMPLETION.json`.
Do not edit policy/evaluator/tournament/governance, fixtures, mutations, public
capture/intake, retained campaigns, outcomes/holdouts, canonical packet, CI,
or execution authority. Do not invent a tenant grant or rewrite protected
evidence. An existing `TENANT` serialization test may be changed only as
needed to assert the new fail-closed run boundary while retaining provenance
round-trip coverage for runnable public evidence.

## Acceptance

1. `validate_scenario` and/or `TemporalWorld` reject any non-`PUBLIC` or
   unknown/blank/malformed `permission_scope` with an I-08-specific invariant
   error before policy invocation or ledger append. A matching `tenant_id`
   alone cannot authorize it. EvidenceEvent construction may still preserve
   the original scope label; do not silently coerce it to PUBLIC.
2. Public evidence follows identical temporal behavior and deterministic
   replay; existing prediction, tenant, and chronology guards still pass.
3. Focused tests prove zero callback invocations and zero ledger records for
   disallowed scopes, acceptance of PUBLIC, and explicit rejection of unknown
   labels. Docs explain the current public-only replay boundary and that
   non-public access would require a separate governed authorization contract.
4. Do not count this slice as full I-01–I-12 or Build Packet #0 acceptance.

## Validation and handoff

Run focused foundation/world tests, freeze source/tests/docs and completion
artifact, then `uv run --python 3.11 --with pytest --with ruff python
scripts/validate.py`. Controller repeats the complete local gate and requests
fresh independent Astra audit on the exact committed candidate. No GitHub,
network, push, merge, or deploy. Do not commit. Preserve others' edits. Default
repair budget: two materially different attempts. Report files, commands, exit
codes, and UNKNOWNs.
