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

`PUBLIC` evidence requires an HTTP(S) source URL and can be acquired through
the implemented `capture-public` command, which runs the Firecrawl CLI for one
public URL at a time. `CONFIDENTIAL` evidence requires a local/source
reference and remains distinct from public evidence. Confidential
attachments must not be committed to or uploaded through the public repository.

Every signal retains a SHA-256 source fingerprint, reviewer, claims, and stable
signal hash. Missing events remain missing; the trace never infers an award,
construction, operation, or power requirement from a later signal.

## Public capture boundary

The explicit `capture-public` command uses Firecrawl for one public URL at a
time and stores raw markdown as a tamper-detecting local capture. Capture is
evidence collection only: it does not extract claims, qualify an opportunity,
 identify a person for outreach, or create an Athena training label. Captures
 must be reviewed before becoming `ProjectSignal` records.

The explicit `review-signal` command requires a named reviewer, exact project
identity, signal type, observed timestamp, claims, and a quote that is present
in the captured source. Accepted signals retain the candidate hash and source
quote so later Athena evaluation can audit the decision boundary.

`backtest-traces` measures lead time from selected early signal types to an
explicit target signal type. Traces without the target, or targets without an
earlier selected signal, remain unresolved. They are not treated as false
alarms until an independently sealed negative outcome exists.

The `resolve-traces` command is the identity boundary. It joins project IDs
only through a hash-bound, reviewer-authored identity review with an exact
quote and source provenance. Conflicting reviews fail closed; no name,
geography, or URL similarity is enough to merge traces automatically.

`build-trace-cohort` creates a local manifest of reviewed traces. It records
each project ID and trace hash, rejects duplicate projects, and re-verifies the
member files when loaded. The cohort is a research container, not a training
label or a claim that every project had a positive outcome.

`backtest-cohort` runs lead-time measurement only after loading and verifying
that manifest. Its report includes both the cohort hash and the backtest hash,
so a result is bound to the exact reviewed evidence set used to produce it.

`seal-trace-outcome` is the retrospective outcome boundary. A reviewer must
explicitly state whether the target was observed, not observed by a cutoff, or
inconclusive, and bind that statement to evidence. The seal also records the
trace hash, target signal type, reviewer, timestamp, and exact evidence quote.
`build-outcome-cohort` groups those seals under the verified trace-cohort hash;
it does not update Athena or claim predictive accuracy.

`evaluate-retrospective` compares the alert status in a cohort-bound backtest
with explicit sealed outcomes only when cohort hashes, target signal types, and
per-project trace hashes all match. It reports true/false positives and
negatives, precision, recall, accuracy, and false-alarm rate. Inconclusive
outcomes and unsealed projects remain visible but are excluded from those
metrics. The evaluation is evidence for later governance review; it does not
promote or modify Athena.

## Athena learning boundary

Athena may later compare signal sequences, lead time, precision, recall, and
false-alarm burden against independently sealed outcomes. It may propose a
ranking or timing change, but it cannot self-promote, turn a correlation into a
fact, or initiate outreach.
