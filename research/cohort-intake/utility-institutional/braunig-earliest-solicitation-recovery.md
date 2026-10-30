# Braunig: first solicitation recovery

Research date: 2026-10-23 (America/Chicago). Agent research only; no named human review, no accepted-cohort entry, and no current opportunity asserted.

## Finding

The earliest **issued solicitation recovered** for the Braunig retirement response is **July 25, 2024**, ERCOT notice **M-C031324-05**, supported by the original **version 1.0 MRA RFP**. December 20 was a second competition. The December 3 board staff paper explicitly identifies July 25 as the original RFP date and reports no qualified proposals. No earlier issued Braunig solicitation was found in the scoped primary-source search.

This is a documented historical event date, **not a proven exact public-availability timestamp under the repository's current date rules**. The dossier remains `INCOMPLETE`, `lead_time.days: null`, `basis: UNVERIFIED`. The former indicative December-based lead time has been removed, not replaced with another unsupported positive number.

## Chronology and date quality

All times below are Central daylight time unless specified. Printed dates, sender timestamps, scheduled events and filing receipts are deliberately distinguished.

| Date | Event | Evidence and interpretation |
| --- | --- | --- |
| March 13, 2024 | ERCOT announces CPS NSOs for Braunig 1-3, proposed suspension March 31, 2025 | Original notice M-C031324-01; public LISTSERV index corroborates sender time 16:10:19 -0500. Earliest recovered public precursor. Notice/sender date only under current proof rules; no rental requirement established. |
| April 22, 2024 | ERCOT finds reliability deficiencies and announces that an MRA RFP will follow | M-C031324-03. More commercially specific than retirement alone, but announcement of future procurement is not the issued solicitation. Printed notice time only. |
| April 23, 2024, 17:33:03 | ERCOT files reliability findings and requests deadline relief | PUCT 55999 item 30 filing receipt. Earliest recovered precursor with an accepted proof kind (`government_docket`); do not backdate its availability to the March event it recounts. |
| May 1, 2024, 13:20:39 | Further good-cause material | Existing item 33 capture preserved; no longer the earliest captured precursor. |
| May 2, 2024 | Deadline exception granted | Described in July 9 filing and original RFP; not independently captured as a new order in this recovery. Avoid confusing the April 23 filing's attached **draft** order with the later actual order. |
| July 9, 2024, 08:49:17 | ERCOT files procurement schedule | PUCT 55999 item 48 receipt; planned July 25 RFP release and July 26 RMR negotiations. A schedule, not an invitation to submit offers. Already discoverable by conventional procurement monitoring. |
| **July 25, 2024** | **First MRA RFP issued** | Version 1.0, notice M-C031324-05, LISTSERV sender time 18:00:30 -0500. Original proposal deadline September 9, 2024, 15:00 CPT. Dossier retains printed minute-level notice time without promoting it to proof. |
| August 9, 2024, 14:56:29 | Docket corroboration of July issuance | PUCT item 53 receipt establishes availability of this retrospective filing, not exact July 25 release. Its cover-letter printed July 18, 2023 is inconsistent with receipt/context and is not used as publication evidence. |
| August 21, 2024 | Revised RFP | December board paper records revision and eventual October 7 deadline. The former August KSAT signal is after first procurement and is removed from `signals`, while its original capture stays intact. |
| December 3, 2024 | Board staff recommendation | Explicit original/revised RFP chronology, no qualified proposals, recommendation for Unit 3 RMR and further mobile-generation work. Staff paper is not itself minutes proving a vote. |
| December 20, 2024 | Second RFP | M-D122024-01 solicits alternatives to proposed use of already-leased mobile generators and Braunig 1-2 RMR. Original capture preserved as later-event evidence. |
| June 4, 2025 | Later emergency-generation agreement effective | Original ERCOT/Life Cycle agreement recites both unsuccessful competitions. Printed effective date is not independently proven publication time. |

## What was being bought, and by whom?

The July RFP sought **seasonal grid-reliability service** for one or more seasons during April 1, 2025-March 31, 2027. Generation, storage and demand response could compete based on cost and their ability to relieve the relevant transmission constraints. An aggregate equivalent reliability benefit of up to the retiring units' capacity is **not** proof of an equivalent rental-generator order.

The original RFP, section 1.1 (PDF page 6), restricts submission and MRA contracting to **Qualified Scheduling Entities (QSEs)**. A rental supplier could potentially support an eligible QSE/resource proposal, but no specific prospective equipment-rental customer was established. Technical eligibility and location matter; retirement MW alone cannot establish a product fit.

| Organization | Role supported by the sources | Commercial implication |
| --- | --- | --- |
| ERCOT | Issuer and reliability-service buyer; eventual emergency-service contracting party | Procurement organization. Original notice names its procurement manager as the historical inquiry contact. |
| QSE bidder | Required contracting route under the original MRA RFP | Potential channel for a supplier; no specific qualified/winning bidder identified. Not a named buyer-path organization. |
| PUCT | Regulator; grants process exceptions | Not the equipment buyer. |
| CPS Energy | Owner of retiring units, RMR counterparty candidate, later site-related participant | Not established as the July rental customer. |
| CenterPoint | Existing lessee under a separate equipment lease | Later redeployment depends on releasing certain existing lease obligations; not a new July Braunig rental purchaser. |
| Prime Power Solutions d/b/a Life Cycle Power | Later mobile-generator owner/operator and ERCOT contractor | Existing supplier, not a prospect to be mislabeled as the end-user buyer. |

The later agreement's recitals F-L distinguish the equipment owner/operator, prior lease and ERCOT service contract. It is a separate commercial arrangement, not evidence of an award under the first MRA competition.

`BRIDGE_OR_INTERIM` is the closest existing schema fit for the bounded seasonal service period. It does **not** certify temporary equipment demand. This dossier must not be counted as a demonstrated rental-positive example without scope review.

## Availability investigation and unresolved result

Preserved evidence includes original notices, the original RFP, PUCT filing receipts, the public LISTSERV index and message bodies, December board material, and the later agreement. All 13 new captures retain the unedited Firecrawl-returned markdown, provider scrape ID, capture time, content SHA-256 and capture hash. See [source manifest](braunig-recovery-source-manifest.json) for URLs and identifiers. These are extracted text captures, not preserved original PDF bytes; extraction fidelity remains a review obligation.

The exact `www.ercot.com` July-notice CDX query returned `[]`; the wildcard hostname/path follow-up did not yield usable content. This is a bounded search result, not proof that no archive exists. LISTSERV message bodies match the relevant notice subject matter, and its index preserves sender dates. A full-header retrieval did not expose an independent receipt timestamp in returned markdown. No accepted exact-date publication proof was recovered. We did not relabel an email archive as a press wire or regulator release merely to pass the validator.

The August docket is useful independent corroboration that the solicitation had happened, but replacing July 25 with August 9 would move the target later and overstate warning. Likewise, a July 9 **planned** release is not proof that release occurred on schedule. No numeric lead time is therefore calculated. The April 23 docket remains a defensible dated precursor; its endpoint is still unresolved for measurement.

Original market-notice pages were sometimes blocked to direct search fetches; Firecrawl returned HTTP 200 content. The current ERCOT RFP index lists current tenders, not the 2024 RFP. The original historical PDF was recovered separately. Earlier public planning outside this scoped record may exist; the result establishes the earliest issued solicitation found, not the first private commercial discussion.

## What this teaches the product

**Inference, not validated performance:** retirement notices can open a research queue; an adverse reliability determination can make that queue commercially specific; a procurement schedule identifies the buyer and deadline. This case supports testing that sequence. It does not yet establish a measured lead-time advantage, a temporary-generation hit, or a reachable rental customer.

Future evaluation must compare against advance procurement scheduling, not only formal tender release. Otherwise a detector could appear early merely by discovering a schedule that a conventional procurement monitor would also find. The case is hindsight-selected and cannot establish live precision or conversion rates.

## Changes and validation

- July 25 replaces December 20 as target; December remains later history.
- March notice, April docket and July schedule added; post-target August article excluded from precursor signals.
- Original captures unchanged; 13 new captures and source manifest added.
- Buyer path restricted to evidence relevant before/at first solicitation; later parties explained separately.
- Status downgraded to INCOMPLETE; counts updated to 13 proposed / 12 incomplete. No review commands or cohort promotion performed.
- Mechanical validator: 25 dossiers, 0 errors, 30 warnings; Braunig: 0 errors and 0 warnings. Existing dossier-validator tests: 90 passed. Mechanical checks do not prove source meaning, historical availability or human review.

Remaining work is evidence acquisition and human scope/date review, not arithmetic. Preserve null lead time until both endpoints satisfy the rules.
