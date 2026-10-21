# INTEGRATE-050 — exhausted Luna repair recovery, narrow state-transition guard

Repo C:/Users/nrsan/Nucleus/02_Projects/Trailforge; branch codex/trailforge-customer-v1;
base cbb10d33c5604e0ed2a1eac668bfbee6c1cba8e7. Single Terra specialist because the
prior Luna's two bounded post-handoff repairs are exhausted. No new architecture.
Canonical return: docs/CUSTOMER_FIRST_V1.md requires normal customer work after
unknown/contradiction demotion, preservation of history, and blocked new fuel work.
Actual constraint: unchanged retained notes must be compared by value across
successive saves; an already-locked previous gate cannot make retained notes new.

Read acceptance-02/REVIEW.json RV4 and actual source. Allowed only operator.py,
tests/test_operator.py, .agent/artifacts/customer-first-048/repair-03/ handoff.
Do not edit graph/state, raw reviews/manifests, product specs, UI/discovery/research,
real databases, remote state. Not alone: preserve all other work.

Acceptance: sourced complete synthetic record may save lawful fuel notes; append
UNKNOWN buyer evidence and reset status NOT_STARTED; first relock retains notes;
at least2 later brief/summary saves retain identical notes and remain locked.
A new/changed nonempty fuel note while locked must still fail; initial locked
record cannot add notes; fuel status PLANNING/COORDINATING must remain blocked.
Do not erase existing note just to allow saves. Evaluate intended invariant,
implement smallest guard repair and meaningful sequential regression. Existing
source requirements and append-only histories unchanged. No test weakening.

Run focused operator+discovery tests, Ruff and diff check; return exact hashes and
COMPLETION.json with real UTC timing/results/UNKNOWN where missing. Controller
will freeze acceptance-03 and run final gates/package/runtime/browser, then fresh
independent review. No self-certification, commit, push, merge, deploy, sending,
or additional agents. Retry budget2 materially different attempts for this packet.
