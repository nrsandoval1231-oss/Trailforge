# South Valley source review packet — 2026-10-01

Status: OWNER-SELECTED CASE; SOURCE/AVAILABILITY ATTESTATION PENDING. No verified fixture or outcome seal created. Canonical Slice3 requires reviewer-approved availability. This note records inspected source claims, not a human attestation.

## Material source findings

1. **Public notice dated April8,2026.** The official April24 supplemental filing includes an affidavit of publication and the actual annexed notice. It identifies South Valley, SV RNO Property Owner1 LLC, 144MW temporary natural gas generation, ninety gas engines, diesel black-start auxiliaries and on-site consumption. Publication is supported to calendar-day precision. Exact public-release instant and timezone are not supplied by the inspected affidavit.
2. **Application filed April20,2026.** The original application text identifies a 144MW-capable system, ninety Jenbacher J420 engines of approximately1.6MW each, Aggreko operation/maintenance and Stabilis LNG operations. It describes expected operation for approximately two to three years until NV Energy supplies permanent service. These are applicant proposal statements, not delivered or operating capacity. This application was recovered from the linked DocumentCloud text view; OCR defects are visible, so do not silently repair or extrapolate ambiguous values.
3. **April24 amendment is evidence of publication, not a capacity change.** It supplements ExhibitH with a formal affidavit. The attached April8 notice says approximately4acres, whereas application descriptions use different footprint/staging measures. No precise acreage claim is admitted; do not merge those measures.
4. **September17,2026 final order conditionally grants the application.** The primary commission order consolidates South Valley26-04026 and Peru Ridge26-04027. Keep projects separate. The dispositive section explicitly bars construction before a permit to construct is issued. South Valley must provide surface-disturbance, construction-stormwater, Class1 OPTC air and county building permits. The Secretary issues a construction permit only after staff verifies compliance. This source does not establish that those conditions were subsequently met, that a procurement award occurred or that the plant operates.

## Source identities and exact retained extracts

### A — original application, mirrored official filing

Source: https://www.documentcloud.org/documents/28069372-dockets-26-04026-original-filing-4-20-2026-epa-uel-svr/?mode=text
Retained file: .firecrawl/s3b-application-full.md
SHA256: 1042BD8D54F95CDED328081342F9E3BCFB142E2F0C55B4BAC4C7FF67922B8444
Relevant spans: original application printed page2 (144MW, engines, operators, bridge rationale); page5 (equipment and fuel); construction-schedule appendix (February2027 expectation, not actual construction).
Acquisition: Firecrawl scrape 01a0f85c-b798-7789-9633-edbb51b2636b. Earlier cover-only scrape is incomplete and not a substitute for this text.

### B — official April24 supplemental filing and publication affidavit

Source: https://puc-onbase.nv.gov/api/Document/ATwAMSw2b%C3%81uI3J4VAn%C3%8157BiuGQLgngwdMOkU0IXh3CaCgTbtZiHVaim21IPazEVvROqawDBXxM2NabijJWrYdW8%3D/?OverlayMode=View
Retained file: .firecrawl/s3b-amendment-full.md
SHA256: 37D317171F71CE8D24424DC413C7A20C5BD978F5035D82B6876C99FA51051CEB
Relevant spans: attorney transmittal explaining ExhibitH supplementation; AFFIDAVIT OF PUBLICATION with April8 date; annexed notice beginning with SV RNO's intent to submit an application. No interpretation of black-start auxiliary generation as the bridge facility's primary fuel.
Acquisition: Firecrawl scrape 01a0f863-bc38-705f-8959-69bfc2f6c188.

### C — official September17 consolidated order

Source: https://puc-onbase.nv.gov/api/Document/AQ%C3%89uCWFk01AzpbKxApzTVhMQs4xWC%C3%89OnJrLb8k9Dc4sOpiWNSDHYvVKZMUR5O%C3%81NDCrdp%C3%81fqNDv8%C3%81TJAqOQrnLvg%3D/?OverlayMode=View
Retained file: .firecrawl/s3b-order-full.md
SHA256: AAC28D4F0EA3582CBE83F3B774F8641D148AE0D728D28FD6C1973F713EEA5815
Relevant spans: title/session date; introduction; summary; paragraph11 reporting applicants'2-3year expectation; dispositive ordered paragraphs1 and3-6. Do not treat later order discussion of earlier testimony as proof that its full content was available on April8 or April20.
Acquisition: Firecrawl scrape 01a0f862-4923-716a-a95e-a895190fe3ea.

## Availability choice requested

The owner was asked whether to use conservative capture-time availability, keeping April8/20/24 and September17 as separately labelled historical calendar dates, or hold historical replay for a separate availability review. No answer has been recorded in this packet yet.

Conservative capture-time replay would admit each inspected source only at or after a recorded observation of its bytes. It demonstrates the real source-backed evidence/decision loop without claiming historical forecasting lead time. An actual historical replay requires approval of document-specific availability bounds; publication of the April8 notice must not expose later application or September order details early. Neither path permits fabricated exact times or sealed outcome metrics.

## Retrieval limitations and security

The official docket's original-application endpoint returned an error JSON payload despite Firecrawl process exit0. That output (.firecrawl/s3b-official-application.md) is rejected as source evidence. The application mirror's complete text is available instead. Official final-order and amended-filing text were actually inspected. No PDF visual-page verification was performed, so OCR-sensitive facts must be checked before final admission. Firecrawl interaction sessions were stopped. Session output files may contain transient browser access URLs; never copy those raw interaction envelopes into tracked evidence. Only public source URLs and content hashes appear here.

No source attestations, field approvals, VERIFIED flags, holdout labels or operating outcomes are implied by the owner's choice of case. No application runtime or existing fixtures changed in this evidence-preparation step.
