# Packet 042 episode

State: full re-audit 040 at `32a536f` returned `CORRECT`, including partial
manifest reproducibility. After packet 041, persisted manifests still dropped
their stored hash on load, and the public world scenario attribute could be
replaced while retaining its constructor hash.

Decision: one Luna packet from local `main` `1319d32` to bind persisted
manifests and temporal-world scenario identity. Action: require and compare
the stored manifest digest, compare local source commit during verification,
and compare the validated scenario hash before each policy step. No policy,
config, fixture, holdout or execution-authority change.

Outcome: exact code candidate `788117148d170b1780a2bcdafaaec8cc29747648`
passed controller local validation (182 tests, compilation, Ruff, three
unsealed bundle checks; exit 0) and independent Astra returned `ACCEPT`.
The builder had two development failures before freeze: tuple round-trip and
Ruff import order; both were corrected and retained in `COMPLETION.json`.
Repair count after audit: 0. Controller direction: `CONTINUE`; full Build
Packet #0 item 15 remains partial.

Attribution: the loader treated the persisted digest as disposable, while
world replay trusted a mutable scenario reference after construction. The
bounded repair checks both at their replay boundaries. Candidate lesson:
validate stored digests on load and recheck mutable inputs before effects;
retain as candidate knowledge, not a promoted rule. Current commit checks do
not detect uncommitted edits or prove policy/config equivalence.

UTC start/finish, planning/build/validation/audit durations, elapsed-to-
accepted, builder model/config identity and token usage: `UNKNOWN` (not
reliably measured). Lane: one Luna builder, one Astra auditor. No speedup claim.
