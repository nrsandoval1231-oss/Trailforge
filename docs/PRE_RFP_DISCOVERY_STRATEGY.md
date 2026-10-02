# Canonical Pre-RFP Discovery Strategy

**Status:** Canonical product/research direction  
**Date:** 2026-10-01

## Product objective

TrailForge exists to discover relevant onsite and distributed-power buying opportunities **before the generation package becomes obvious, publicly commoditized, or difficult to influence**.

A published RFP is one observable downstream event, but it is not the whole target. TrailForge must also detect projects that may buy through private RFQs, contractor packages, direct sourcing, negotiated procurement, long-term service agreements, or other non-public channels.

The operating objective is:

> Find a credible power-buying opportunity early enough to identify the responsible customer or contractor, start a useful conversation, and influence the solution before the generation package is committed.

Canonical commercial sequence:

```text
EARLY SIGNAL
  -> PROJECT / FACILITY / OPERATING NEED
  -> POWER-NEED HYPOTHESIS
  -> PROCUREMENT / BUYING-EVENT HYPOTHESIS
  -> DIRECT BUYING CHAIN
  -> CUSTOMER CONTACT
  -> VERIFIED POWER NEED
  -> SOLUTION
  -> FUEL STRATEGY
```

Fuel providers remain downstream solution partners, not the primary discovery channel.

---

## 1. Learn from historical procurements, but predict the underlying buying event

TrailForge should build a corpus of **relevant historical and current power procurements**, including expired solicitations, awarded solicitations, canceled solicitations, rebids, private buying events where verifiable, and unresolved cases.

For each case, reconstruct the complete procurement family where available:

- original notice
- solicitation/RFP/RFQ
- technical specifications
- drawings and attachments
- amendments
- bidder questions and answers
- intent-to-bid requirements
- site visits
- award notices
- cancellations
- rebids
- contract execution
- project completion or other downstream outcomes

The research question is not merely:

> What did the RFP ask for?

It is:

> What project, operating problem, reliability condition, schedule constraint, facility change, utility limitation, or construction milestone made this procurement necessary — and what public evidence of that condition existed before the buying event became obvious?

Backward reconstruction:

```text
KNOWN RELEVANT POWER PROCUREMENT
        ↓
What problem was the customer solving?
        ↓
What physical project or operating change created that problem?
        ↓
What earlier records revealed that change?
        ↓
When did those records actually become publicly available?
        ↓
What was the earliest defensible reason to investigate or call?
        ↓
Would a general discovery policy have found that evidence without knowing the future project name?
        ↓
Can the resulting pattern identify other opportunities?
```

Historical reconstruction generates candidate hypotheses. It does not by itself prove predictive value.

---

## 2. Relevant opportunity scope

TrailForge should focus on **onsite, distributed, temporary, bridge, commissioning, prime, supplemental, and behind-the-meter electrical generation opportunities** with realistic commercial relevance.

Initial high-priority verticals include:

### Data centers
- construction power
- commissioning power
- phased energization
- utility bridge power
- delayed permanent service
- onsite operating generation
- behind-the-meter generation
- expansion phases
- large electrical shutdowns or energization transitions

### Remote aggregate, quarry, and mining operations
- new quarry or mine development
- remote crushing, screening, conveying, washing, or processing loads
- dewatering
- plant expansions
- fixed-site electrification
- temporary power during utility extension
- remote prime power

### Utilities and cooperatives
- temporary generation capacity
- local reliability support
- generation replacement
- isolated service
- planned outages
- delayed permanent infrastructure
- project-specific capacity constraints
- temporary capacity while durable resources are developed

### Industrial and institutional facilities
- facility expansions
- plant modifications
- electrical shutdowns
- continuity requirements
- major maintenance
- onsite energy projects
- capacity additions
- temporary power during construction or switchgear/substation work

### Water and wastewater
- treatment-plant expansions
- pumping loads
- bypass operations
- construction outages
- temporary generation packages
- remote or constrained utility service

### Fixed oil and gas infrastructure
- compression
- SWDs
- gas processing
- production electrification
- gathering and midstream facilities
- fixed-site infrastructure

Mobile rig/frac work is not the default target unless explicitly supported by a distinct commercial strategy.

Behind-the-meter is a **power architecture**, not an industry. It may appear across several verticals.

---

## 3. Relevance must be multidimensional

Keyword matching is insufficient. Every case or live record should be classified independently across at least four dimensions.

### A. Power activity

Examples:

- construction
- commissioning
- bridge
- remote prime
- temporary reliability
- behind-the-meter
- supplemental capacity
- outage continuity
- operational generation
- backup/emergency only
- maintenance/service only

Do not infer a temporary rental requirement merely because a permanent standby generator appears in a document.

### B. Facility / industry context

Classify the physical environment and use case:

- data center
- utility
- aggregate/quarry/mining
- industrial
- institutional
- water/wastewater
- fixed oil and gas
- other supported category

### C. What is being purchased?

Distinguish:

- generation rental
- equipment purchase
- temporary-power service
- long-term delivered power
- PPA / energy service
- engineering/design
- installation
- maintenance
- fuel-only supply
- unrelated electrical equipment

A document that mentions generators is not automatically a generator-rental opportunity.

### D. Commercial / technical fit

Evaluate separately from basic relevance:

- activity-specific MW or defensible range
- duration
- start window
- duty cycle
- redundancy
- voltage / electrical interface
- fuel constraints
- location
- project timing
- procurement stage
- buying path
- incumbent / awarded status
- remaining scope

For 2G-oriented evaluation, retain the approximate 300 kW-and-up commercial floor while allowing unknown-size opportunities to remain researchable. Unknown MW must not be discarded merely because the project is early.

**Collect broadly -> classify precisely -> qualify commercially.**

---

## 4. Find power packages inside larger projects

TrailForge must inspect broad construction, infrastructure, facilities, utility, and operating procurements for embedded generation requirements.

A relevant power opportunity may appear inside:

```text
Parent Project
  -> Prime Contract
      -> Electrical Scope
          -> Temporary / Commissioning / Bridge Generation Requirement
```

This can expose buyer paths through:

- owner
- developer
- utility
- EPC
- GC
- electrical contractor
- commissioning contractor
- facilities contractor
- project procurement team

Do not equate:

> "The parent contract contains a generation requirement"

with:

> "The generation package is still open."

TrailForge must investigate whether that scope is retained by the owner, delegated, already awarded, subcontracted, separately procured, or otherwise unavailable.

---

## 5. Two operating lanes

TrailForge should support two distinct but connected discovery lanes.

### Lane 1 — Pre-RFP / pre-buying-event prediction

Primary purpose: reach the buyer early.

Potential precursor sources and events include:

- capital plans
- board and council agendas
- budgets
- grants and awards
- economic-development agreements
- facility plans
- engineering studies
- design awards
- consultant scopes
- site acquisition
- zoning / entitlement
- environmental proceedings
- air permits
- utility plans
- service filings
- interconnection material
- reliability studies
- construction permits
- electrical permits
- equipment procurements
- contractor awards
- procurement forecasts
- incumbent contract expiration
- sources-sought notices
- pre-solicitations
- market research notices

### Lane 2 — Active procurement

Primary purpose: never miss an actionable live opportunity while the predictive system matures.

Monitor:

- procurement portals
- active RFPs
- RFQs
- IFBs
- sources sought
- pre-solicitations
- attachments
- amendments
- Q&A
- site visits
- intent-to-bid deadlines
- due-date changes
- bidder lists where public
- cancellation / rebid
- award notices

The active-procurement lane is immediately useful and also creates new training/evaluation cases.

---

## 6. Evidence and temporal integrity

TrailForge must preserve the difference between:

- **event_date** — when the real-world event happened
- **document_date** — date printed or associated with the record
- **verified_available_at** — earliest defensible time the evidence was publicly available
- **observed_at** — when TrailForge first captured it
- **prediction_date** — when a policy actually surfaced the opportunity

Historical replay must use only evidence available at the cutoff.

A document published later that describes an earlier event cannot be credited as evidence at the earlier event date.

If historical availability cannot be established, mark it explicitly and exclude it from strict early-warning credit.

Preserve original versions where documents or pages can change over time. Later edits must not rewrite earlier replay state.

---

## 7. Separate backtrace from genuine discovery

Two tests are required.

### Backtrace test

Given a known procurement or project, can TrailForge reconstruct earlier evidence that would have justified investigation?

This is useful for hypothesis generation.

### Discovery test

Without supplying the future project or RFP name, would the configured source feeds and general discovery policies actually have surfaced the precursor evidence?

Only this earns genuine discovery credit.

Searching historical records using a known future project name is allowed for research, but the result cannot be presented as proof of independent early discovery.

---

## 8. Negative and unresolved cases are mandatory

A corpus containing only successful procurements will overfit badly.

Include comparable projects that:

- were canceled
- were delayed
- received adequate utility service
- solved the need another way
- bought an incompatible solution
- never produced an observed procurement
- remained private
- remained unresolved by the evaluation cutoff
- produced irrelevant generation scopes
- had generation scope already awarded
- looked promising but proved commercially unsuitable

Do not treat "no public RFP found" as proof that no buying event occurred.

Use explicit outcome states such as:

- relevant procurement observed
- private buying event verified
- canceled
- supply resolved
- incompatible solution
- awarded before detection
- project delayed
- no outcome observed by cutoff
- unknown

UNKNOWN remains UNKNOWN.

---

## 9. Holdouts and hindsight control

TrailForge must test policies on unseen cases.

Rules:

- hold out whole procurement/project families, not individual documents from the same family
- keep amendments and awards with their parent case
- maintain untouched validation/holdout cases
- include later time-period holdouts
- include unseen buyers, geographies, and verticals where possible
- do not let future evidence leak into replay
- do not let a model rely on memorized future facts where avoidable
- mask identifying names during model-assisted tests when useful
- preserve policy/version lineage

Finding a historical pattern is hypothesis generation.

Predicting an unseen outcome from then-available evidence is validation.

---

## 10. Sealed-holdout promotion gate

A normal holdout is not sufficient for production-policy promotion. TrailForge must preserve a **sealed holdout** whose membership and expected evaluation procedure are fixed before the candidate policy is tested.

Minimum sealing evidence:

- immutable list of holdout case/project-family IDs
- cohort version and content hashes for the replay inputs used by those cases
- timestamp showing the seal predates candidate-policy evaluation
- candidate policy/version hash fixed before holdout execution
- evaluator/version identifier
- replay configuration and cutoff rules
- machine-readable result artifact with per-case outcomes
- aggregate metrics used for the promotion decision
- retained failures, UNKNOWNs, and regressions rather than only successful examples
- evidence that the holdout cases were not moved into development/training after seeing candidate results

The sealed holdout must remain untouched during candidate lesson development. If a case is exposed, corrected in a way that changes the evaluation target, or otherwise invalidated, record that explicitly and reseal a new version rather than silently reusing the old claim of independence.

Athena promotion requires:

1. zero hard-invariant failures,
2. required robustness/regression checks,
3. sealed-holdout evidence,
4. minimum metric floors,
5. objective improvement over the frozen baseline under the same attention/evaluation budget.

The evidence bundle for promotion must be reproducible from retained artifacts. A narrative claim that a policy "performed better" is insufficient.

---

## 11. Sequence patterns matter more than isolated keywords

TrailForge should learn temporal combinations and project-state transitions.

Candidate pattern families are hypotheses to test, not established rules.

### Data-center bridge power

Possible sequence:

```text
phase schedule advances
  -> construction/electrical activity becomes visible
  -> project-specific permanent power timing appears later
  -> possible bridge window
```

Invalidators may include adequate existing supply or an already-awarded package.

### Remote aggregate / mining power

Possible sequence:

```text
site/plant expansion
  -> fixed processing equipment appears
  -> operating schedule advances
  -> documented service limitation or remote-site condition
  -> prime/temporary power hypothesis
```

### Utility temporary capacity

Possible sequence:

```text
specific reliability/capacity need
  -> durable solution cannot meet required date
  -> temporary-resource planning
  -> procurement
```

### Facility outage continuity

Possible sequence:

```text
electrical replacement / substation / switchgear project
  -> planned outage
  -> operations must continue
  -> temporary generation scope
```

### Onsite operating generation

Possible sequence:

```text
defined load / resilience requirement
  -> feasibility / engineering
  -> environmental or utility work
  -> budget / procurement progression
  -> generation buying event
```

### Rebid / replacement

Possible sequence:

```text
relevant procurement
  -> cancellation / failed award / supplier issue
  -> underlying need remains
  -> new buying window
```

The useful pattern is the meaning, order, timing, and relationship of evidence to one physical project or operating requirement.

---

## 12. Athena is the learning loop

TrailForge should implement Athena as the mechanism that improves discovery and research policy from outcomes.

Canonical Athena loop:

```text
State
 -> Decision
 -> Action
 -> Outcome
 -> Attribution
 -> Candidate Lesson
 -> Gauntlet
 -> Validated Experience
 -> Policy
 -> Next Decision
```

TrailForge mapping:

### State
Only evidence legitimately available at the historical/live cutoff.

### Decision
Examples:
- ignore
- watch
- investigate
- deepen research
- identify buyer
- surface for customer discovery

### Action
Examples:
- inspect another source
- follow a project record
- research service timing
- search for contractor assignment
- inspect procurement status
- investigate buyer path
- recommend a specific discovery call

### Outcome
Examples:
- relevant procurement appears
- private purchase is verified
- need disappears
- power is solved
- project is canceled
- generation scope is awarded
- record was irrelevant
- result remains unknown

### Attribution
Determine which evidence, signal family, query, research action, and decision policy contributed to a correct or incorrect result.

### Candidate lesson
Examples:
- source combinations that consistently surfaced projects earlier
- event sequences that were predictive
- misleading patterns that created noise
- better order of research actions
- more useful buyer-path research
- source additions suggested by repeated missed opportunities

### Gauntlet
Challenge the lesson using:
- unseen cases
- counterexamples
- negative cases
- prior successful policies
- time-separated holdouts
- regression checks
- action-burden comparison

### Validated experience / policy
Only lessons that improve objective results without violating hard constraints may become candidate policy updates.

No Athena artifact self-promotes.

Athena V1 improves behavior by changing validated policy/experience, not by rewriting TrailForge source code or retraining model weights.

---

## 13. Athena should learn research order, not only prediction

One of the highest-value learning targets is:

> Which missing fact should TrailForge investigate next because it is most likely to change whether the opportunity deserves attention?

Examples:

- permanent energization timing
- whether temporary generation is already awarded
- actual activity-specific MW
- project construction start
- contractor assignment
- procurement ownership
- whether a new processing plant is grid-connected
- whether a utility has already secured a resource

Athena should evaluate research actions by:

- decision value
- cost
- latency
- uncertainty reduced
- effect on buyer accessibility
- effect on commercial qualification

This allows TrailForge to become faster and cheaper while improving signal quality.

---

## 14. Source learning

Historical cases should also teach TrailForge where valuable precursor evidence originates.

A winning pattern may reveal useful sources not previously prioritized:

- consultant reports
- utility attachments
- board packets
- engineering scopes
- contractor procurement pages
- environmental records
- capital-improvement schedules
- equipment bids
- reliability studies
- grant documentation

Source value should be judged by **contribution to early, correct, actionable discoveries**, not document count.

A high-volume source that generates noise is not inherently valuable.

---

## 15. Jev, generative research, Athena, and deterministic code have separate jobs

### Retrieval / acquisition
Firecrawl or source-specific connectors retrieve and preserve public evidence.

### Deterministic code
Owns:
- timestamps
- replay cutoffs
- identifiers
- exact matching rules
- arithmetic
- scenario calculation
- policy thresholds
- state transitions
- evaluation metrics
- persistence
- immutable history
- Athena promotion gates

### Jev
Use as a fast bounded judgment layer where useful.

Candidate Jev jobs:

- relevant electrical-generation scope?
- procurement stage?
- same project/procurement family?
- generation rental vs purchase vs maintenance vs fuel-only?
- meaningful change?
- worth deeper research?
- which research action class should be considered?

Jev must support UNKNOWN and schema-constrained outputs. Schema validity does not equal factual correctness. Evaluate Jev before granting it decision authority.

### Generative research model
Use for deeper synthesis:

- reconstruct project/procurement history
- interpret long technical scopes
- find missing buyer evidence
- reconcile conflicting records
- prepare account/opportunity briefs
- propose candidate explanations or lessons

The model does not override source evidence or deterministic evaluation.

### Athena
Learns which policies and research strategies improve outcomes over time.

Athena does not become another crawler, another database, or an autonomous code-rewriting layer.

---

## 16. Evaluation objective

Primary metric:

```text
useful_lead_time =
    buying_event_or_obvious_milestone
    - first_actionable_detection
```

A first actionable detection should generally include:

- identifiable project/site/facility
- supported power-need hypothesis
- a plausible responsible organization or buyer path
- a concrete reason to investigate/contact

It does not require perfect MW or duration if the project is still early.

Track:

- useful lead-time distribution
- percentage surfaced before procurement
- percentage surfaced while the package remained influenceable/open
- project identification accuracy
- opportunity relevance
- missed relevant opportunities
- buyer-path availability at first surface
- action burden
- false-positive burden
- UNKNOWN/unresolved rate
- source contribution
- research cost
- model/Jev cost
- time to qualification
- customer-call outcomes

Evaluate policies under a comparable attention budget, for example the same number of surfaced opportunities per week.

Do not optimize raw alert count.

---

## 17. Real-world feedback closes the loop

Customer and pursuit feedback is high-value evidence.

Capture outcomes such as:

- real need confirmed
- project real, timing wrong
- wrong buyer
- correct buyer
- package already awarded
- utility power adequate
- generation not in scope
- need delayed
- no response
- opportunity lost
- opportunity quoted
- opportunity won
- fuel strategy selected

"No response" is not automatically a negative label.

User feedback must remain attributed and time-stamped. It can influence future learning only through the Athena validation path.

---

## 18. Relationship to GridLens

TrailForge and GridLens should not become duplicate operational systems.

**TrailForge is the proving ground.**

It:

- reconstructs historical project/procurement timelines
- tests precursor hypotheses
- runs counterfactual replay
- evaluates Jev/model judgments
- learns research policies
- measures useful lead-time advantage
- validates candidate signal/source policies

**GridLens is the operational live-discovery surface.**

Validated TrailForge signal policies, source strategies, and research lessons can be promoted deliberately into GridLens.

Do not build a generalized shared framework before the two systems demonstrate a truly identical abstraction in working code.

---

## 19. Immediate execution plan

### Phase 1 — Relevant procurement corpus

Build approximately 30-50 deeply reconstructed power-project/procurement families.

Include:

- current and expired RFPs
- awards
- cancellations / rebids
- active solicitations
- matched negative/look-alike projects
- unresolved cases
- multiple target verticals
- public and, where verifiable, non-RFP buying outcomes

Scan broadly for candidates, but reconstruct the smaller cohort thoroughly.

### Phase 2 — Timeline reconstruction

For each case:

1. identify procurement/buying outcome
2. reconstruct the underlying physical project/operating need
3. capture complete document family
4. locate earlier precursor evidence
5. verify public-availability dates
6. identify buyer path at each relevant cutoff
7. identify invalidating/negative evidence
8. freeze the replay timeline

### Phase 3 — Baseline policies

Start simple.

Examples:

- deterministic source/event combinations
- basic temporal rules
- simple buyer-accessibility rules
- bounded Jev classifications where measured value exists

Do not start with elaborate forecasting machinery.

### Phase 4 — Athena evolution

Use case outcomes to propose lessons.

Compare:

- baseline policy
- Athena-enhanced policy

on untouched holdout cases.

Promote only validated improvements.

### Phase 5 — Forward live proof

Run validated policies prospectively without known project names.

Freeze predictions when made.

Measure:

- actual live detection time
- buyer accessibility
- relevance
- eventual procurement/buying outcome
- commercial usefulness

Historical potential lead time and actual live lead time must remain separate metrics.

---

## 20. First success criterion

TrailForge does **not** need to prove universal forecasting across every vertical before becoming useful.

The first meaningful success is:

> At least one repeatable, source-backed precursor pattern identifies commercially relevant onsite/distributed-generation opportunities materially before conventional RFP/procurement monitoring, on unseen or prospective cases, with tolerable false-positive/action burden and an identifiable customer or contractor path.

An already-public RFP does not satisfy this criterion by itself.

A single anecdotal historical case does not satisfy this criterion.

---

## 21. Non-goals

Do not:

- build a generic RFP aggregator
- optimize for procurement-document volume
- equate generator keywords with relevant generation opportunities
- treat all data-center or utility projects as power opportunities
- assume lack of a public RFP means no procurement occurred
- use future evidence in replay
- convert UNKNOWN to negative
- let models invent load, timing, buyers, or outcomes
- create a giant ontology
- create another governance/orchestration layer
- allow Athena lessons to self-promote
- automatically push unvalidated lessons into GridLens
- make fuel suppliers the primary upstream discovery target
- rebuild working TrailForge infrastructure merely to match GridLens implementation details

---

## Canonical product statement

> TrailForge learns how onsite and distributed-power buying opportunities develop. It reconstructs past procurement trails, tests which early signals genuinely predicted relevant demand, and searches for those same conditions unfolding now — so the responsible customer can be reached before the generation package is committed.

**The procurement archive supplies cases. Historical project evidence supplies precursor hypotheses. Athena determines what actually generalizes. Live discovery proves whether that learning creates commercial advantage.**
