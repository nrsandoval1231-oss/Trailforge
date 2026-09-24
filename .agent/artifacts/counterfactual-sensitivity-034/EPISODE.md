# Episode: counterfactual-sensitivity-034

State: The independent 20-item Build Packet #0 audit at `b73dd45` found
counterfactual false positives: a changed evidence ID changed the replay hash
even when a policy ignored the decisive fact. Packet 033 had already been
accepted locally; packet 034 started from `e62df7a`.

Decision: make case expectations explicit and compare substantive policy
answers. Keep `BASELINE_A`, retained fixtures, Arena authority, and the local
validation gate intact.

Action: Luna implemented material comparisons and per-case pass results. The
first exact candidate `a89751a` received Astra `CORRECT` because a confidence-
only response could pass. A repair at `dac2ed4` received `CORRECT` because
missing confidence becoming numeric could pass a stability case. The final
repair at `bd8d2a6` rejects both false positives. Raw reviews remain in
`REVIEW-1.json` and `REVIEW-2.json`.

Outcome and evaluation: Controller ran the complete local gate on `bd8d2a6`:
exit 0, 137 tests, compilation, Ruff, and three bundle checks. Astra returned
`ACCEPT` for this bounded packet. `BASELINE_A` still fails the cancellation
counterfactual; no real-world forecasting claim or policy promotion follows.

Attribution: replay hashes measured provenance changes, while confidence-only
changes measured an asserted certainty rather than a substantive response.
Candidate lesson: required counterfactuals need a semantic response predicate;
stability checks must reject unsupported certainty increases. This lesson is
retained here, not promoted beyond this packet.

Next direction: `CONTINUE` with a bounded power-profile accounting repair for
Build Packet #0 item 9, followed by the complete local gate and independent
audit. The full 20-item acceptance audit remains open.
