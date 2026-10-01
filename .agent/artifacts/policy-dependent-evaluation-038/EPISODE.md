# Episode: policy-dependent-evaluation-038

State: Independent Build Packet #0 re-audit at `501efe7` returned `CORRECT`
and found visibility-only discovery/lead-time scoring. Audit documentation
was accepted and locally merged at `129b0ee` before this packet began.

Decision: require an explicit policy episode claim with a visible evidence
reference. Preserve absent precision and known-truth recall misses. Use local
validation only and retain the research-only boundary.

Action: Luna changed the evaluator and synthetic tests. Astra returned
`CORRECT` at `57c1450`: repeated claims inflated precision and unrelated
weather evidence could earn useful lead time. Raw rejection is retained in
`REVIEW-1.json`. The repair deduplicated claimed episodes and left replay
useful lead unavailable because the current evidence schema cannot prove
episode linkage or customer-action sufficiency.

Outcome and deterministic evaluation: Controller ran the complete local gate
on exact code candidate `03b0d7f`: exit 0, 158 tests, compilation, Ruff,
and three bundle checks. Astra returned `ACCEPT` for this bounded packet.
Discovery remains a mechanical episode-ID comparison against explicit policy
claims; correctly guessed IDs citing unrelated visible evidence may still
receive discovery credit. No real-world accuracy or full evaluator acceptance
is established.

Attribution: evaluator access to visible evidence was confused with a policy
prediction; repeated claims then distorted precision. Candidate lesson:
score explicit policy output, deduplicate alerts by identity, and abstain
where evidence sufficiency cannot be proven. Retain without promotion beyond
the audited slice.

Next direction: `CONTINUE` with a bounded typed episode-linkage and
customer-action sufficiency contract before useful lead can be scored or a
full all-controls comparative campaign can claim meaningful lead-time metrics.
