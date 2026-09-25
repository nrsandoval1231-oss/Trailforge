# Packet 041 episode

State: independent full re-audit 040 on `32a536f` returned `CORRECT`, with
I-08 permission enforcement partial. The only explicit runnable evidence
grant in current replay was `PUBLIC`; tenant matching did not authorize other
scopes.

Decision: one bounded Luna packet from base `da1138b` to enforce I-08 before
policy exposure. Action: reject non-`PUBLIC` scopes in scenario validation and
revalidate at each `TemporalWorld.step` because callers can replace the public
scenario attribute. Preserve evidence labels, research-only authority and
all protected evidence.

Outcome: exact code candidate `cc48a469c99ac02cadde01d67d3ec280a7a6590d`
passed the controller's complete local gate (174 tests, compilation, Ruff,
three unsealed bundle checks; exit 0) and independent Astra returned `ACCEPT`.
Repair count: 0 after candidate freeze. Controller direction: `CONTINUE`.
This is bounded I-08 replay proof, not full Build Packet #0 acceptance.

Attribution: the scenario previously carried `permission_scope` but
`TemporalWorld` did not authorize it before policy callback. The added check
removes that path for current public-only replay. Candidate lesson: check
authorization at the effect boundary as well as construction when mutable
object references can be replaced; retain as candidate knowledge, not a
promoted rule. The existing public-scenario replacement/hash binding issue is
outside this packet and remains open.

UTC start/finish, planning/build/validation/audit durations, elapsed-to-
accepted, builder model/config identity and token usage: `UNKNOWN` (not
reliably captured). Lane: one Luna builder, one Astra auditor. No speedup claim.
