# TrailForge Operator UI — Vision

Status: Draft for owner approval, 2026-10-21. Governed by
[CANONICAL_VISION.md](CANONICAL_VISION.md); where they disagree, the canonical
vision wins.

## Why this exists

TrailForge has a working mining engine but no interface that matches how the
owner works. Two partial UIs exist, and neither serves the job:

| UI | Where | Strength | Problem |
| --- | --- | --- | --- |
| Research workbench (`trailforge-ui`) | `main` | Wired to replay and mining reports | Engine-testing tool; ~140 lines of JS; not an operator surface |
| Jade operator desk (`trailforge-operator`) | `codex/trailforge-customer-v1` | Solid storage, append-only evidence, edit conflicts, fuel gate | Built for the superseded Oct 1 data-center direction; generic project model; not connected to the mining engine; ~40% of the first screen is slogan |

This document defines **one** operator UI that replaces both.

## The one-line vision

> Open TrailForge and know, within ten seconds, which mining power requirement
> deserves your next hour, why, and what is still unknown.

## User

Single operator: Nick, a business development lead with an engineering background.
Local, single-user, desktop-first. Nobody else sees this screen in this phase.
That means:

- **Density over polish.** Tables, compact cards, and keyboard speed beat hero
  banners and marketing copy. No slogans on working screens.
- **Engineering honesty.** Units, phases, sources, and unknowns are always visible.
- **No presentation mode yet.** Sharing views come later, with an explicit
  confidentiality review (see Phase 4).

## Jobs to be done (in order of frequency)

1. **Triage.** See which requirements changed, what's newly actionable, and what's
   gone stale.
2. **Assess one project.** Understand phases, loads, timing, dependencies, buying
   chain, and supplier fit on one page.
3. **Capture and review evidence.** Add a source, attach excerpts to claims, mark
   facts reviewed, and resolve conflicts.
4. **Decide the next action.** Research a gap, identify a contact, or prepare a
   conversation brief (never send).
5. **Log what happened.** Record conversations and outcomes so forecasts can be
   scored later.

## Product principles (non-negotiable)

1. **Requirement is the unit, not the project.** A mine has several phase-specific
   requirements (early works, construction, commissioning, bridge, operations).
   They are never summed into one MW figure.
2. **Every value shows its basis.** It is labeled `REPORTED`, `ESTIMATED`,
   `INFERRED`, `CONFLICT`, or `UNKNOWN`, together with its source and date. Color
   never carries meaning alone.
3. **Unknown is a first-class state.** Unknown is shown as a research gap with a
   suggested next step, not hidden and not treated as a failure.
4. **Need before supplier.** The neutral requirement view shows no 2G branding or
   fleet filter. Supplier fit sits in its own panel, after the need.
5. **No outbound action exists.** Briefs and drafts can be copied. Nothing can be
   sent from the UI.
6. **Time-safe.** Source published, first observed, and available dates stay
   distinct and visible. The UI never presents later knowledge as if it had been
   known earlier.
7. **Confidential stays local.** Private documents are marked and never mixed into
   shared or public evidence.

## Information architecture

Four screens. Each answers one question.

### 1. Queue: "What deserves my attention?"
The default screen. Dense table of **requirements** grouped by project:

| Column | Example |
| --- | --- |
| Project · phase | Stibnite · construction |
| Load | 2 MW normal / UNKNOWN peak (basis tag) |
| Needed by | 2027-Q2 (ESTIMATED) |
| Procurement | Open · Awarded · Delegated to EPCM · UNKNOWN |
| Fit (supplier) | Viable · Excluded (diesel-only) · Unknown |
| Evidence strength | Count of reviewed vs. unreviewed claims |
| Next action | "Confirm EPCM power package owner" |
| Changed | New source 2 days ago |

Filters for phase, procurement state, fit, and stale-or-changed, plus keyboard
navigation. A thin strip at the top counts what changed since the last visit.

### 2. Project dossier: "What do we know and not know?"
One page per project. Layout from top to bottom:

1. **Header facts.** Owner, operator, EPCM, location, commodity, stage, existing
   power, each with its basis tag.
2. **Requirement timeline.** Horizontal phases with load, needed-by, and
   grid-ready-by dates. Dependency lines connect them (e.g. "grid late → bridge
   need").
3. **Requirement cards.** One per phase: demand envelope, delivery constraints,
   procurement status, and its open unknowns.
4. **Buying chain.** Organizations → people → role → the evidence for that role.
   Authority is never assumed.
5. **Supplier fit panel.** Hard exclusions, viable classes, and engineering
   unknowns. Visibly separate from the need.
6. **Next action and brief.** A copyable brief with no send control.

### 3. Evidence: "Is this true?"
A source library and a review queue:
- Captures with their three dates, access rights, and hash.
- Claim → excerpt mapping, plus a "mark reviewed" control that requires the
  reviewer's name.
- A conflict view that shows competing claims side by side, so you decide
  instead of the system choosing silently.

### 4. Activity: "What happened?"
A log of conversations and outcomes (qualified, disqualified, won, lost,
unresolved), linked to the requirement it concerns. This feeds later forecast
scoring.

The Research Arena (replay and campaigns) stays a separate developer tool, linked
from settings rather than from the main navigation.

## Visual direction

- **Brand:** the approved Trailforge Jade system (`brand/trailforge-v1/tokens.css`),
  with the Trailmark logo instead of a text wordmark, Manrope for text, and IBM
  Plex Mono for data and dates.
- **Layout:** a full-height graphite rail, then content. Light theme by default,
  with a dark theme from the tokens.
- **Density:** 14–16px body text and compact table rows. No hero banner on any
  working screen.
- **States:** each basis tag uses text plus shape plus color.
- **Responsive:** desktop is primary. Phone width (390px) must work without
  overlap or horizontal scroll, for reading on the road.

## Architecture direction

- **Backend:** keep the Python modular monolith. Carry over the branch's operator
  storage (SQLite, versioned documents, append-only evidence, stale-edit
  rejection, loopback session auth) and adapt its document model to the mining
  requirement contract. Do not port the Microsoft/QTS feed logic as the default
  discovery source.
- **Engine:** the UI reads the existing mining pack outputs (requirements,
  qualification, supplier screening). No business logic in the browser.
- **Frontend:** stay dependency-free if practical (plain JS modules, CSS tokens),
  so it stays packaged with the Python install. Revisit a framework only if the
  dossier interactions need one.
- **One command** to launch: `trailforge-ui`.

## Phases

| Phase | Delivers | Done when |
| --- | --- | --- |
| **0. Salvage** | Port the operator storage and tests onto `main`; drop the stale brand copies | Branch tests pass on `main`; branch can be archived |
| **1. Read-only core** | Queue and project dossier over existing mining imports | The synthetic copper project plus one real project render fully on desktop and phone |
| **2. Evidence loop** | Capture, review, conflict resolution, append-only corrections | A real source goes from capture to a reviewed claim without editing JSON |
| **3. Action loop** | Next-action brief, buying chain editing, activity log, fuel/supplier gate | A full cycle from new signal → brief → logged conversation is recorded |
| **4. Later** | Presentation/share view, multi-supplier, background discovery | Only after phases 1–3 prove useful in real use |

Retire the old `trailforge-ui` workbench and the Jade desk at the end of Phase 1.

## Risks

| Risk | Mitigation |
| --- | --- |
| Polished UI implies more certainty than the evidence supports | Basis tags everywhere; unknowns count shown per requirement |
| Another UI rebuild that doesn't get used | Phase 1 is read-only and small; judge it on real projects before building Phase 2 |
| Data model drift between operator storage and mining contract | One schema: the mining requirement contract wins |
| Scope creep into CRM or outreach | No send, no CRM sync, no enrichment in phases 1–3 |
| Confidential data in screenshots or shares | Local only; a share view requires a separate confidentiality review |

## Success criteria

- Nick opens TrailForge instead of a spreadsheet for mining power work.
- The best next action on any tracked requirement is visible within 10 seconds.
- No requirement is shown without its basis, source date, and unknowns.
- Phase 1 renders without errors at 1366px and 390px, with no overlap or
  horizontal scroll.
- Within 30 days, at least one real requirement reaches a logged qualified
  conversation through the UI.

## Explicitly not building

Hosted service, multi-user accounts, outbound email/LinkedIn, CRM sync, paid data
enrichment, autonomous crawling, price quoting, and forecast accuracy claims.
