# Episode: negative-knowledge-036 and context revision 036b

State: Build Packet #0 audit at `b73dd45` found in-memory only negative
knowledge. Packet 035 had been accepted and locally merged at `5d422ec`
before this work began.

Decision: persist rejected lessons as hash-checked local snapshots and reuse
them only with matching content and evaluation context. Keep Athena research
only and all promotion gates unchanged. Use local validation only.

Action: Luna added snapshot save/load and optimizer reuse. Astra returned
`CORRECT` at `f40c66e` for bool/int equality and repeated candidate execution,
at `800285e` for seed/evaluation-context omission, and at `c9a5fd7` for a
handpicked context list missing `world.py` and `foundation.py`. Raw verdicts
remain in `REVIEW-1.json` through `REVIEW-3.json`. After the default repair
budget was exhausted, the controller returned to the canonical requirement
and issued revised packet 036b. The revised implementation fingerprints both
complete local Arena source packages.

Outcome and deterministic evaluation: Controller ran the complete local gate
on exact code candidate `711b5b8`: exit 0, 156 tests, compilation, Ruff,
and three bundle checks. Astra returned `ACCEPT` for this bounded mechanism.
No sealed holdout, authenticated rejection decision, policy promotion, or
real-world accuracy is established.

Attribution: in-memory state lost rejections; ordinary Python equality erased
typed distinctions; a partial source manifest allowed stale reuse. Candidate
lesson: durable negative knowledge needs typed content identity and a complete
replay-context identity before it suppresses evaluation. Retain this lesson
without general promotion beyond the audited packet.

Next direction: `VALIDATE` with a fresh independent 20-item Build Packet #0
acceptance audit on the integrated exact candidate, using only the complete
local gate and repository evidence. Preserve UNKNOWN sealed outcomes and
research-only authority.
