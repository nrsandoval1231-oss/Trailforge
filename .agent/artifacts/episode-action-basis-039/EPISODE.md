# Packet 039 episode

State: local `main` at `b597373762bcafcba4cb400841f2a11e552d9fc6`;
Build Packet #0 re-audit `CORRECT`; useful lead unavailable without typed
episode/action support. Decision: one bounded Luna packet on a separate local
branch. Action: add an optional reviewer attestation, conservative evaluator,
DSL/schema round trip, synthetic tests, and documentation.

Outcome: first exact candidate `4f1639f` passed 162 local tests but Astra
returned `CORRECT`: a mixed invalid discovery basis could earn lead, and a
future-reviewed attestation was visible to policy. Repair 1 reused the complete
discovery eligibility and hid future-reviewed annotations from policy state.
Exact repaired code candidate `33131a06970e035cbc4cad4a1da80eb1fdd6d84d`
passed the independent local gate (163 tests, compilation, Ruff, three bundles;
exit 0) and Astra returned `ACCEPT`. Repair count: 1. Controller direction:
`CONTINUE`; full Build Packet #0 remains open.

Attribution: the first evaluator checked for any matching attested member of
the basis instead of requiring the whole claim to meet its discovery rule. The
world also exposed the attestation as soon as base evidence was visible. The
repair aligns lead qualification with discovery and review-time visibility.
Candidate lesson: when a downstream metric uses a policy claim, reuse the
claim's complete eligibility predicate and independently verify every cited
evidence item against the scenario. This is retained as a candidate lesson,
not promoted policy. Real-world attestation accuracy, sealed outcomes, holdout
comparison, and policy promotion remain `UNKNOWN`.

UTC start/finish and planning/build/audit durations: `UNKNOWN` (not measured
reliably). Lane: one Luna builder, one Astra auditor. Builder model/config
identity and token usage: `UNKNOWN`; no speedup claim. Elapsed-to-accepted:
`UNKNOWN`.
