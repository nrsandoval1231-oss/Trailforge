# Cohort intake (20-50 historical projects)

Status: no case is human-reviewed. Everything under `research/cohort-intake/` is a **proposal**. Current
counts are whatever `scripts/check_cohort_dossiers.py` prints (see "Running the validator"); they are generated
by the validator, not asserted here, and a proposal does not count toward the 20-50 target until a named human
has reviewed it and it has passed the checklist below.

## Purpose

`docs/FINISH_READINESS.md` defines the finish test: which signal families would have put us in front of real
power projects materially earlier than conventional discovery, and who could we have approached at that time?
Answering it needs roughly 20-50 historical projects, each with a reconstructed chronology, a verified
downstream milestone and source-backed dates. This document is the intake process that produces those
chronologies without letting invented or unreviewed evidence reach the cohort tooling.

## Dossier lifecycle

1. **Capture.** Freeze each primary source with `capture-public` (or `capture_markdown`/`capture_with_firecrawl`
   in `athena_procurement_arena.public_capture`). A capture records URL, retrieval time and content SHA-256.
2. **Propose.** A research agent writes a dossier `research/cohort-intake/<vertical>/dossiers/<project_id>.json`
   (`trailforge-cohort-dossier-v0`) with status `PROPOSED_UNREVIEWED` (or `INCOMPLETE` when evidence is missing).
3. **Validate.** `scripts/check_cohort_dossiers.py` must exit 0. This is a mechanical gate only (see "What the
   validator does not prove").
4. **Human review.** A named human works through the reviewer checklist below. For each signal that survives, the
   path from capture to a reviewed `ProjectSignal` is the existing `review-signal` command
   (`--capture`, `--signal-id`, `--project-id`, `--signal-type`, `--signal-title`, `--observed-at`,
   `--source-quote`, `--claims-json`, `--reviewed-by NAME`, `--output`), which re-checks the quote against the
   capture and records the reviewer. Dossiers themselves must never contain `verified_by` or any review claim.
   - `buyer_path` from the dossier must be copied into the `ProjectSignal` `claims["buyer_path"]`
     (`signal_family_report._has_buyer_path` reads exactly that key; a dossier-level `buyer_path` is invisible
     to the report).
   - `ProjectSignal` has **no confidence field**. A `PRINTED_DATE_ONLY` or `UNKNOWN` signal therefore cannot
     enter the cohort as a proven date: re-prove its availability date (then it is `PROOF_CITED`) or exclude it.
5. **Identity review.** `resolve-traces` (see `docs/PRE_RFP_*.md`).
6. **Cohort.** `build-trace-cohort`.
7. **Report.** `compare-signal-families` for lead time, coverage, action burden and buyer-path availability.

## Dossier schema (`trailforge-cohort-dossier-v0`)

The schema string is unchanged, but the rules below replace earlier drafts (`VERIFIED_TIMESTAMP(S)` tokens are now
errors; see "PROOF_CITED is not verification").

```
{ "schema_version": "trailforge-cohort-dossier-v0",
  "status": "PROPOSED_UNREVIEWED" | "INCOMPLETE",
  "project_id": "lowercase-slug",            # ^[a-z0-9][a-z0-9-]{2,79}$, equals the file name stem
  "project_name", "location", "owner_or_developer", "selection_note": "...",
  "vertical": "us-mining" | "intl-mining" | "data-center" | "utility-institutional",  # equals the parent directory
  "signals": [ {
      "signal_id": "unique within the dossier",
      "signal_type": "<SignalType value, NOT PROCUREMENT_SIGNAL>",   # see signal_ledger.py
      "title": "...",
      "observed_at": "ISO-8601 WITH timezone, year >= 1990",
      "availability_confidence": "PROOF_CITED" | "PRINTED_DATE_ONLY" | "UNKNOWN",
      "availability_evidence": {"kind": "sec_edgar|exchange_announcement|government_docket|wayback_cdx|wire_timestamp|printed_date|other",
                                "url": "...", "note": "..."},
      "source_url": "http(s) URL, equal to the capture's source_url",
      "capture_path": "repo-relative path inside research/cohort-intake/<vertical>/captures/",
      "capture_id": "equal to the capture file's capture_id",
      "source_sha256": "64 hex, equal to the capture's content_sha256",
      "source_quote": "exact contiguous text from the capture content, >= 20 chars",
      "claims": { } } ],
  "target": null | { ...same shape..., "signal_type": "PROCUREMENT_SIGNAL", "target_description": "..." },
  "target_fit": "TEMPORARY_OR_RENTAL|BRIDGE_OR_INTERIM|ONSITE_LONG_TERM_SUPPLY|PERMANENT_PLANT_OR_GRID|PERMIT_OR_STATUS_ONLY",
  "target_fit_note": "why the target does or does not match temporary-power demand (>= 20 chars)",
  "later_procurement_events": ["optional free-text strings: awards etc. after the target"],
  "buyer_path": [ {"organization", "role": "OWNER|DEVELOPER|EPC|EPCM|GC|ELECTRICAL_CONTRACTOR|UTILITY|OTHER",
                   "evidence_signal_id": "a signal_id or the target's", "quote": "exact text from that signal's capture"} ],
  "lead_time": {"days": number | null, "basis": "PROOF_CITED_TIMESTAMPS" | "UNVERIFIED",
                "earliest_signal_id": "...", "note": "..."},
  "blockers": ["..."], "reviewer_checklist": ["..."],
  "created_by": "...", "created_at": "ISO-8601 WITH timezone" }
```

Unknown or missing fields are errors (`target_fit`, `target_fit_note` are required whenever `target` is not null;
`target_fit`, `target_fit_note` and `later_procurement_events` are otherwise optional). `PROPOSED_UNREVIEWED` needs
at least two signals; every signal that is present (in either status) must pass all evidence checks.
`INCOMPLETE` marks a case with known evidence gaps and must have `lead_time.days` null and basis `UNVERIFIED`. A
`null` target is allowed in either status: the project stays **unresolved**, which is not the same as negative. The
validator prints a warning for it.

### The target, and `target_fit`

`PROCUREMENT_SIGNAL` is allowed **only** as `target`, never in `signals[]`, because
`signal_family_report.py` takes the earliest `PROCUREMENT_SIGNAL` in a trace as the downstream target.

**Earliest-procurement rule (reviewer-enforced, not mechanical).** The target must be the earliest
procurement-type event in the chain. If an earlier tender, RFT, proposal solicitation or letter of intent exists, it
is the target; later awards and contracts go in `later_procurement_events` (or notes). Otherwise lead time is
overstated.

`target_fit` states what kind of demand the target represents: `TEMPORARY_OR_RENTAL`, `BRIDGE_OR_INTERIM`,
`ONSITE_LONG_TERM_SUPPLY`, `PERMANENT_PLANT_OR_GRID`, or `PERMIT_OR_STATUS_ONLY`, with a note of at least 20
characters. The last two draw the warning "reviewer: consider target null": they are allowed, but a permanent plant
or a permit/status event is usually not the downstream temporary-power milestone, and the reviewer should consider
leaving the project unresolved instead.

## The date rule

`observed_at` is the moment the public version of the document was **demonstrably available**, not the date
printed on it. Acceptable proof types (`availability_evidence.kind`):

- `sec_edgar` (EDGAR acceptance timestamp), `exchange_announcement` (exchange/regulator release time),
  `government_docket` (docket entry or filing timestamp), `wayback_cdx` (a Wayback/CDX capture timestamp showing the
  page existed), `wire_timestamp` (press-wire release time).
- `printed_date` and `other` are **not** proof of availability.

Rules enforced mechanically:

- `PROOF_CITED` requires a `kind` that is **not** `printed_date` and **not** `other`, an http(s) proof `url` and a
  non-empty `note`.
- `PRINTED_DATE_ONLY` and `UNKNOWN` must use `kind` `printed_date` or `other`; if the date can be proven, upgrade the
  confidence instead.
- `observed_at` must carry a timezone, have a year of at least 1990, must not be in the future, must not be after
  the capture's own `captured_at`, and no signal may be after the target.
- Lead time is "proof cited" only when the earliest signal **and** the target are both `PROOF_CITED`. Then
  `basis` is `PROOF_CITED_TIMESTAMPS` and `days = (target.observed_at - earliest.observed_at)` in days (tolerance
  0.01, offsets respected), and `earliest_signal_id` must really be the earliest signal. In every other case
  (including a null target, and every `INCOMPLETE` dossier) `days` must be `null` and `basis` `UNVERIFIED`. A printed
  date alone therefore never yields a lead time.
- A `wayback_cdx` signal whose `source_url` is not itself a `web.archive.org/web/<14-digit timestamp>id_/...`
  snapshot gets a warning: Wayback proves the URL existed, not that this text did; capture the snapshot or treat the
  date as an upper bound.

### PROOF_CITED is not verification

`PROOF_CITED` means only that a human-checkable proof is *cited* (kind, URL, note). It does **not** mean anyone has
verified it. All confidence values are agent-asserted until a named human reviews them. In particular, Wayback
snapshots and ASX/exchange listings that the agent fetched but did not capture are upper bounds / uncaptured proofs:
the reviewer must open them. The old tokens `VERIFIED_TIMESTAMP` and `VERIFIED_TIMESTAMPS` are rejected with a
pointer to the new names, because nothing in a dossier may read as "verified".

## The exact-quote rule

For every signal, the target and every `buyer_path` entry the validator loads the capture through the repo's own
`load_capture` (which re-hashes content and checks `capture_hash`), then requires:

- `capture_path` is a repo-relative POSIX path (absolute paths, `//server/share`, drive letters, backslashes and `..`
  are rejected) that resolves, after following symlinks, inside `research/cohort-intake/<vertical>/captures/`;
- the capture file has no duplicate JSON keys;
- `source_sha256` equals the capture's `content_sha256`, `capture_id` and `source_url` equal the capture's;
- `source_quote` (and `buyer_path[].quote`, checked against the capture of its `evidence_signal_id`, not any other
  capture) is an **exact contiguous substring** of the capture `content`. **No normalization at all** is applied: not
  whitespace collapsing, not case folding, not quote-mark or ellipsis handling. If the capture has a line break in
  the middle of a sentence, the quote must include that line break; choose a shorter quote that does not span it
  if that is awkward.
- Quotes under 20 characters are an **error**; 20-39 characters is a warning. A `buyer_path` quote that contains
  none of the organization's words of 4+ letters is a warning. A numeric value in `claims` whose digits (commas
  ignored) do not appear in the signal's `source_quote` is a warning ("claim not literally supported by quote").

Dossier files themselves are parsed with duplicate-key detection at any depth; a repeated key is a per-file error.

## What the validator does not prove

It checks that quotes exist in the **stored** capture file and that the capture file is self-consistent (content hash
and capture hash). It cannot prove that the capture is a faithful copy of the live source: the initial batch
has provider `firecrawl` and empty `provider_job_id` values. Later captures may retain provider scrape IDs,
which aid retrieval auditing but do not independently prove historical publication or faithful extraction. It also cannot prove
that a quote means what the dossier says, that a date proof is genuine, that the project identity is right, or that
the target is the earliest procurement event. Those are the human reviewer's job.

## Forbidden in a dossier

No `verified_by` key, and no key named or containing `verified` (other than keys starting with `unverified`),
`reviewed`, `review`, `reviewed_by`, `approved`, `approved_by`, `human_review`, `signed_off` or `signed_by`, at any
depth, including inside `claims`. No string value that is just a review claim (`verified`, `reviewed`, `approved`,
`confirmed`, `signed off`, `human reviewed`, any `VERIFIED*` token), trailing punctuation ignored (`"Verified."` is an
error). Prose inside quotes, notes and checklists may use the words normally.

## Running the validator

```
uv run --python 3.11 --extra dev python scripts/check_cohort_dossiers.py                 # default --root research/cohort-intake
uv run --python 3.11 --extra dev python scripts/check_cohort_dossiers.py --json          # machine output
uv run --python 3.11 --extra dev python scripts/check_cohort_dossiers.py --root path/to/dir
```

It reads `<root>/*/dossiers/*.json`, collects **all** errors per dossier (it does not stop at the first), prints
PASS/FAIL lines with every error and warning, then a summary table
(`project_id | vertical | status | signals | target | lead-time basis | errors`) and totals. Exit code is 0 only
when no dossier has an error; 2 if the root is missing, or if an explicit `--root` contains no dossiers (the default
root with no dossiers prints a message and exits 0). A file that cannot be parsed (invalid JSON, duplicate keys,
excessive nesting) is reported as that file's error and the run continues. Warnings (do not fail the run):
single-source dossier, `source_url` reused by another project, quote shorter than 40 characters, no target, weak
`target_fit`, unsupported numeric claim, buyer organization absent from its quote, Wayback source that is not a
snapshot URL. Also errors: duplicate `project_id` across files, file name != `project_id`, `vertical` != directory.

Tests: `tests/procurement_arena/test_cohort_dossiers.py` (no network).

## Selection caveat

Cases are chosen in hindsight: someone knows these projects eventually reached procurement. The cohort is
therefore a **development set**, not a holdout. Lead-time numbers from it can show whether a signal family is
worth building a detector for; they are not a forecast of live hit rates. Do not tune and evaluate on the same
cases and call the result validated.

## Unresolved is not negative

A project with no verified target signal stays unresolved. It is never counted as a miss or a false alarm, and
should be kept in the cohort so coverage is not inflated by dropping hard cases. Record in `blockers` what was
searched and not found.

## Human reviewer checklist

A named reviewer must complete this for each dossier before any `ProjectSignal` is created or `--reviewed-by` set:

1. **Re-fetch or diff a sample of captures** against the live page or a Wayback snapshot; the validator cannot tell
   a faithful capture from an altered one.
2. Open each captured source and confirm the `source_quote` actually supports the `signal_type` and `claims`
   (the validator only proves the text exists, not that it means this).
3. Confirm the capture is the right document for the right project; settle identity (name, owner, location,
   aliases) and that the target concerns the same project.
4. Independently check each `PROOF_CITED` proof in `availability_evidence` (open the URL; Wayback and exchange
   listings the agent did not capture are uncaptured proofs); downgrade to `PRINTED_DATE_ONLY` if the proof does not
   show public availability at `observed_at`. Re-prove or exclude `PRINTED_DATE_ONLY`/`UNKNOWN` signals.
5. Confirm the target is a genuine downstream procurement event with its own source, that it is the **earliest**
   procurement-type event (earlier tender/RFT/LOI becomes the target), that `target_fit` is honest (consider a null
   target for `PERMIT_OR_STATUS_ONLY` / `PERMANENT_PLANT_OR_GRID`), and that every signal truly precedes it.
6. Confirm each `buyer_path` entry names the organization in that role in the cited text, not by inference.
7. Check selection bias: note why this case was chosen and whether it is biased toward success.
8. Recompute lead time by hand; then create each `ProjectSignal` with `review-signal --reviewed-by NAME` (copying
   `buyer_path` into `claims["buyer_path"]`), and run `resolve-traces` -> `build-trace-cohort` ->
   `compare-signal-families`.
9. Keep cases without a target as unresolved.

