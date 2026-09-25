# Packet: policy-dependent-evaluation-038

Status: READY. Base: `129b0ee0c8d54980e7fb88432fe41c59bc2be0ee`
on `codex/policy-dependent-evaluation-038`. Owner: one Luna builder.
Dependency: independent full Build Packet #0 re-audit at `501efe7` returned
`CORRECT`; this is its single next bounded direction, targeting evaluator
item 6 and first-campaign metric integrity.

## Objective and canonical rule

Build Packet #0 v1.0 requires discovery precision/recall, earliest actionable
detection, misses/false discovery, and useful lead time measured from the
first actionable detection with enough evidence for a real customer action.
Vague guesses must receive no early credit. `evaluate_replay` currently
credits the truth episode merely when its ID is visible in policy input;
constant `IGNORE` can get full discovery credit, and lead time starts at
visibility rather than policy output.

## Allowed files and exclusions

Own `src/athena_procurement_arena/evaluation.py`, directly affected
`tests/procurement_arena/test_evaluation.py` and `test_campaign.py`,
`src/athena_procurement_arena/campaign.py` only if aggregate handling must
change, `docs/EVALUATION.md` for the explicit output contract, and completion
artifacts under `.agent/artifacts/policy-dependent-evaluation-038/`.
Do not change policy logic, fixture truth, canonical packet, historical
campaign report, tournament/promotion gates, execution authority, CI, or
protected evidence.

## Acceptance

1. Define a minimal explicit, machine-readable policy discovery claim in the
   existing forecast mapping: an episode ID and nonempty basis evidence IDs.
   Score it only when those basis IDs were visible at the frozen decision time.
   No inference from the evaluator's access to `visible_evidence_ids` alone.
2. Constant `IGNORE` and a policy with only a vague/unsupported guess receive
   no discovery or useful-lead credit. An explicit correct evidence-supported
   claim can earn discovery credit; an explicit wrong claim counts against
   precision. No explicit prediction basis leaves precision/lead time
   `UNKNOWN`/unavailable while a known positive truth can still count as a
   recall miss.
3. Useful lead time requires an evidence-supported correct claim and a real
   actionable recommendation such as `PREPARE` or `BID_REVIEW`; early `WATCH`
   or vague `RESEARCH` receives no lead-time credit. Use the existing
   `useful_lead_time_seconds` helper and preserve temporal cutoff/replay.
4. Regression campaign aggregation remains deterministic and handles absent
   precision without inventing a value. Adjust tests that previously asserted
   full recall from mere visibility; assert meaningful discrimination between
   `IGNORE` and an evidence-supported policy in synthetic mechanics only.
5. Keep all missing real-world outcomes/holdout claims `UNKNOWN`. This packet
   does not claim complete evaluator, all-controls campaign, or policy quality.

## Validation and handoff

Run focused affected tests, freeze implementation and completion artifact,
then run `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`.
Controller independently repeats the complete local gate and commissions
Astra audit on the exact local commit. No GitHub/network validation. Do not
commit, push, merge, or deploy. Preserve others' work. Default repair budget:
two materially different attempts. Report exact files, commands, exit codes,
and UNKNOWNs.
