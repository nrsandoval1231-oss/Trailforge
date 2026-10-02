# Project Signal Tracing

Project signal tracing is now the center of TrailForge.

## Purpose

Reconstruct what could actually have been known about a real power project before the opportunity became obvious, then measure whether a candidate signal policy would have surfaced it early enough to matter commercially.

Each trace retains canonical project identity, source-backed signal events, observed/available timestamps, provenance, a later verified downstream comparison milestone, buying-chain evidence available at relevant times, and explicit UNKNOWN values.

Potential signal families include site/land activity, utility/interconnection events, construction milestones, contractor awards, electrical work, permitting, equipment constraints, energization delays, commissioning preparation, gas infrastructure, and other evidence. These are hypotheses until tested.

## Lead-time calculation

`lead_time_advantage = conventional_milestone_time - first_valid_policy_surface_time`

Only source-backed timestamps count. Unsupported boundaries remain unresolved.

## Buyer path

At first surface, record whether public evidence could identify a plausible end customer/project owner, EPC, GC, electrical contractor, or other party responsible for project power. Do not treat a fuel provider as the primary buyer path. Fuel selection follows customer discovery and confirmation of the requirement.

## Cohort

Next target: approximately 20-50 real projects. Expose both hits and misses so signal families can be judged by lead time and action burden.


## Procurement and buying-event tracing

Historical RFPs, RFQs, awards, cancellations, rebids, and other verified buying events are downstream anchors for reconstructing precursor evidence. A trace should move backward from the buying event to the physical project or operating need, then identify what could actually have been known earlier.

Keep two tests separate:

1. **Backtrace:** given the known project/procurement, could earlier evidence have justified investigation?
2. **Discovery:** without supplying the future project or RFP name, would configured source feeds and general policies have surfaced that evidence?

Only the second earns independent discovery credit.

Relevant traces should distinguish power activity, facility/industry context, what is actually being purchased, and commercial/technical fit. Generator keywords alone are insufficient. Parent-project contracts may contain embedded electrical or temporary-generation packages; preserve the distinction between a generation requirement and an actually open generation package.

Sequence hypotheses, source combinations, and buyer-path rules are candidates for Athena evaluation. They do not become production policy until they pass sealed-holdout and regression checks described in the canonical [Pre-RFP Discovery Strategy](PRE_RFP_DISCOVERY_STRATEGY.md).
