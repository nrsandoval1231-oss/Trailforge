# Project signal tracing

Trailforge's Phase 2 signal ledger records the chronology that can precede a
power procurement event. It is deliberately separate from the current
opportunity shortlist: a project can be historically valuable for learning even
when it is no longer actionable.

## Signal chronology

Typical signal types include project announcement, feasibility completion,
permit filing or approval, EPCM award, construction approval, quantified power
requirement, fuel selection, procurement signal, construction start, and
operation. The ledger sorts signals by observed timestamp and exact signal ID;
the earliest signal is a deterministic property, not a model judgment.

## Evidence classes

`PUBLIC` evidence requires an HTTP(S) source URL and can be acquired through a
future controlled public-capture adapter. `CONFIDENTIAL` evidence requires a
local/source reference and remains distinct from public evidence. Confidential
attachments must not be committed to or uploaded through the public repository.

Every signal retains a SHA-256 source fingerprint, reviewer, claims, and stable
signal hash. Missing events remain missing; the trace never infers an award,
construction, operation, or power requirement from a later signal.

## Athena learning boundary

Athena may later compare signal sequences, lead time, precision, recall, and
false-alarm burden against independently sealed outcomes. It may propose a
ranking or timing change, but it cannot self-promote, turn a correlation into a
fact, or initiate outreach.
