# Packet: negative-knowledge-036

Status: READY. Base: `5d422ecffb9debbff7158731741adcd8558ac9aa` on
`codex/negative-knowledge-036`. Owner: one Luna builder. Next `CONTINUE` node
after accepted packet 035, targeting Build Packet #0 item 13. Research only.

## Objective and evidence

The controlling Build Packet #0 v1.0 (SHA-256
`7abb4c4aeb6ab049ea1f2f8888f76bc4f9e96daa3217797b07706bf7858236d8`)
requires rejected lessons/negative knowledge to persist so failed ideas are
not rediscovered repeatedly. Current `NegativeKnowledge` is one in-memory
dictionary; `test_negative_knowledge_persists_rejected_lessons` checks only
same-instance retention. `run_athena_optimization` does not consult it.

## Allowed files and exclusions

Own `src/athena_procurement_arena/governance.py`,
`src/athena_procurement_arena/athena_optimizer.py`, directly affected
`tests/procurement_arena/test_governance.py` and `test_athena_optimizer.py`, and
completion artifacts under `.agent/artifacts/negative-knowledge-036/`.
Do not edit the canonical packet, fixtures, policy logic, promotion thresholds,
CI, protected evidence, execution authority, or unrelated work.

## Acceptance

1. Persist rejected `CandidateLesson` records to a versioned, deterministic,
   hash-verified local JSON snapshot and load them into a fresh instance.
   Reject malformed, altered, duplicate-ID, or mismatched-schema snapshots;
   do not silently overwrite an existing snapshot.
2. Keep a rejected lesson's identity and exact content together. A changed
   lesson under the same ID must not be silently treated as the same rejected
   idea or overwrite old negative knowledge. Provide a safe conflict result.
3. A later Athena run supplied with a loaded store must visibly skip the
   exact previously rejected lesson before candidate-policy/tournament work,
   while retaining a machine-readable reason and preserving other candidates.
   No store supplied retains current deterministic behavior. Do not skip a
   changed lesson solely because its ID matches.
4. Tests prove save/load across instances, tamper/duplicate/conflict rejection,
   and a second optimization run reusing rejection. No self-promotion or
   real-world accuracy claim follows. Keep holdout unavailability fail closed.

## Validation and handoff

Run focused affected tests, then freeze implementation/completion artifact
and run `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`.
Controller independently repeats the full local gate and commissions Astra
audit on the exact local commit. No GitHub/network validation. Do not commit,
push, merge, or deploy. Preserve others' work. Default repair budget: two
materially different attempts. Report exact files, commands, exit codes,
and UNKNOWNs.
