# Packet: episode-action-basis-039

Status: READY. Base: `b597373762bcafcba4cb400841f2a11e552d9fc6` on
`codex/episode-action-basis-039`. Owner: one Luna builder.

## Objective

Build Packet #0 defines useful lead as procurement time minus the first
actionable detection, where enough evidence supports a real customer action.
Current replay deliberately leaves that metric unavailable: a policy's cited
visible ID has no typed episode linkage or customer-action sufficiency proof.
Add an optional reviewer-attested evidence annotation and consume it only for
the correct episode, cited evidence, supported action, and temporal cutoff.
This is a mechanics contract, not a finding about real-world outcomes.

## Allowed files and exclusions

Own `src/athena_procurement_arena/foundation.py`, `scenario_dsl.py`,
`evaluation.py`, package `__init__.py` only for the new type export,
`schemas/procurement-arena-scenario-v1.schema.json`, directly affected
`tests/procurement_arena/test_foundation.py`, `test_evaluation.py`,
`test_scenario_dsl.py` (or existing equivalent), `docs/EVALUATION.md`, and
`.agent/artifacts/episode-action-basis-039/COMPLETION.json`.
Do not edit policies, fixtures, canonical packet, campaign report, CI,
protected evidence, promotion gates, or execution authority. Do not invent
real-world reviewed annotations.

## Acceptance and invariants

1. Define a typed, immutable optional action-support attestation on an
   `EvidenceEvent`: exact episode ID, action from `PREPARE`/`BID_REVIEW`, named
   reviewer, review time, exact source span belonging to that event, and a
   nonblank review rationale or equivalent specific basis. Reject malformed
   attestations, prediction evidence, contradictory evidence, and impossible
   review chronology. Legacy evidence without annotation remains valid.
2. Round-trip the optional annotation through the versioned scenario DSL,
   JSON schema, and stable scenario hash. Do not mutate existing fixtures.
3. Replay can score useful lead only from a hash-valid frozen decision on the
   same scenario whose explicit discovery claim names the truth episode and
   cites the attested evidence ID. Recheck the cited ID against scenario
   evidence and actual visibility at decision time; reviewer attestation must
   already exist at that time, and the recommended action must match the
   attested action. `WATCH`, `RESEARCH`, unsupported/wrong episode claims,
   unrelated visible facts, missing review, post-decision review, post-
   solicitation detections, and tampered decisions earn no lead credit.
   Select the earliest qualifying decision. Preserve discovery scoring contract
   from packet 038 and `None` for genuinely unavailable lead.
4. Tests cover positive synthetic mechanics and all critical negative cases,
   including DSL round trip. Do not label synthetic proof as real-world
   accuracy or completion. Explain the reviewer-attestation trust boundary in
   `docs/EVALUATION.md`.

## Validation and handoff

Run focused affected tests. Freeze source, tests, docs, and completion artifact;
run `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`
once on that candidate. Controller independently repeats this complete local
gate and audits the exact local commit with Astra. No network or GitHub checks.
Do not commit, push, merge, or deploy. Preserve others' edits; repair budget is
two materially different attempts. Record changed files, commands, exit codes,
and remaining UNKNOWNs.
