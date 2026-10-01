# Episode: arena-invariant-repair-033

State: Build Packet #0 audit of `b73dd45` returned `CORRECT` for mutable nested
forecasts and false-clean invariant status. Commit `24c7990` later recorded
that audit and became packet 033's base; the repository was clean on `main`.

Decision: repair only those two hard-invariant surfaces on local branch
`codex/arena-invariant-repair-033`; use the complete local validation gate and
independent strategic audit. No GitHub CI is used as validation.

Action: Luna implemented deep freezing, explicit dataclass rejection, I-10
world/evaluator checks, and fail-closed campaign/CLI statuses with behavioral
tests. Controller reran the complete local gate on each frozen candidate. The
first independent audit returned `CORRECT` for a mutable dataclass alias;
its exact verdict is retained in `REVIEW-1.json`. A distinct repair rejected
dataclass forecast values before ledger construction.

Outcome and deterministic evaluation: exact code commit `4dc86a5` passed the
complete local gate (133 tests, compilation, Ruff, and three fixture checks;
exit 0). The second independent audit returned `ACCEPT` for packet 033 only.
The reviewer found no execution-authority expansion. The full Build Packet #0
audit and real-world forecasting evidence remain open.

Attribution: shallow freezing caused the ledger alias; unconditional campaign
status and missing world/evaluator I-10 checks caused false-clean results.
Candidate lesson: a frozen decision must reject any canonical value type it
cannot detach, and every hard invariant must affect reported run status.
This lesson is retained here, not promoted as a general policy without a
separate cross-packet validation metric and reversal plan.

Next direction: `CONTINUE` with one bounded counterfactual-sensitivity packet.
Require a change in forecast/action or a justified invariant result, not merely
a changed replay hash when evidence IDs differ. Keep research-only authority and
UNKNOWN real-world outcomes.
