# OPERATOR-048-R2: repair independent FIX, same integrated branch

Repository C:/Users/nrsan/Nucleus/02_Projects/Trailforge; branch codex/trailforge-customer-v1;
base cbb10d33c5604e0ed2a1eac668bfbee6c1cba8e7.
Read acceptance-01/REVIEW.json under .agent/artifacts/customer-first-048.
Retain its raw FIX and source manifest unchanged. This is repair-only, not new scope.
No state/graph/completion promotion, commit, push, merge, deploy or real data edits.

Own operator.py, operator_assets/app.js, tests/test_operator.py and quickstart text
strictly needed to explain reviewed source requirements; evidence in
.agent/artifacts/customer-first-048/repair-02/. Discovery code is frozen.
Not alone: preserve controller evidence and all other edits.

Resolve RV1: REVIEWED scope/buyer requires a real traceable HTTP/HTTPS source URL
with hostname (current supported public-source model; no new file resolver).
Reject malformed/empty required locator on write and never promote it in gate.
Keep source optional for UNKNOWN intake. Make UI label/validation reflect this.
Tests must assert both store persistence rejection and direct gate fail-closed.
No need to assert that a syntactically valid URL proves truth: human review remains.

Resolve RV2: while gate locked reject new/changed nonempty fuel notes on store/API
write, even status NOT_STARTED. Preserve previously lawful saved fuel notes when a
later contradiction relocks the gate; do not delete history just to pass. Compare
prior state transactionally. Tests: blank early project with fuel notes rejected;
legally saved notes retained on contradiction; attempted changed notes blocked.

Resolve RV3: prefer removing duplicated client localGate; display only returned
server gates. Save new evidence with fuel status reset conservatively if needed,
then consume server result. Do not mutate current.gate optimistically on failed
save. Existing append/interaction sequence must work; UNKNOWN active buyer relocks
and displays blocked. Regression via HTTP and controller browser after handoff.

Run focused tests/Ruff/JS syntax; full gates deferred to new exact candidate freeze.
Return repair COMPLETION.json with exact files/hashes, UTC start/end, failed/success
attempt evidence, limitations. This is the second bounded post-handoff repair for
this builder, materially distinct from XML repair. If blocked, report evidence
without expanding authority or silently weakening contract.
