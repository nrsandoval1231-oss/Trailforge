# Episode: power-profile-accounting-035

State: Build Packet #0 audit item 9 at `b73dd45` found that a 10 MW need
with 4 MW known dependable supply yielded a 6 MW primitive gap but a 10 MW
profile gap. Packet 034 was locally accepted and merged before this packet
began at `b35294f`.

Decision: reconcile the primitive and piecewise profile under the packet's
`G(t)` rule; retain UNKNOWN and I-12, and evaluate mixed unknown profiles
without asserting a numeric peak. Use local validation only.

Action: Luna made the primitive derive its peak from temporal segments and
credited non-additive supply claims conservatively. Astra returned `CORRECT`
for first candidate `be28472` because surplus baseline from one scope could
transfer to another. The repair caps each baseline claim at its own need load;
raw rejection is retained in `REVIEW-1.json`.

Outcome and evaluation: Controller ran the complete local gate on exact code
candidate `c3fe02e`: exit 0, 142 tests, compilation, Ruff, and three bundle
checks. Astra returned `ACCEPT` for this bounded packet. No real-world power
forecast accuracy or full Build Packet #0 acceptance is established.

Attribution: the profile ignored known baseline supply, and the initial
global maximum allowed unsupported cross-scope surplus transfer. Candidate
lesson: model time slices first, then cap source-specific supply before
combining claims with uncertain independence. Retain this lesson without
general promotion until broader cases validate it.

Next direction: `CONTINUE` with durable negative knowledge for Build Packet
#0 item 13, then rerun the local gate and independent audit. Full packet
acceptance and sealed holdout evidence remain open.
