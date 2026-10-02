# HC-001 availability recovery review — FIX

Candidate: staged tree `752733dbe61b91b77a7343ab2a5d45bb2fdd1db5`, base `9d49bcbbbf4207b657c1658f2e476742251fadf3`. This is a review of the bounded recovery/reporting slice, not historical commercial measurement or product completion.

## Blocking finding

The recovered Crusoe input says `buyer_path.status: ORGANIZATION_IDENTIFIED_AUTHORITY_UNKNOWN` and cites an archived Lancium statement that Crusoe would own and develop the campus. That supports the organization's identity and availability at the early snapshot. It does not identify procurement authority, a responsible contact, or a direct buying chain. Yet `historical_cohort.py:297-299,331-336` marks `buyer_path.status` as `SUPPORTED` when an organization string and timely capture exist, and the generated `report.md` displays `Crusoe (availability SUPPORTED)` in a column labeled Buyer path. The JSON and Markdown can therefore be read as a supported buyer path when only organization availability is supported. Preserve the cited organization and time, but make authority, contact, and chain UNKNOWN in the machine report and visible table. Test the supported-organization/unknown-authority case. Do not change the fixed signal policy, replay engine, or source evidence.

## Other evidence and limits

The five identities and fixed policy are retained. Crusoe's two official-URL archive snapshots support a 21,354,908-second observation interval, not first market availability or rental demand. Montauk's policy snapshot follows its target snapshot; this is a late-observation control, not a miss. The City of Memphis bulletin is distinct from the Chamber source; xAI's selected power target remains UNKNOWN. The compound Montauk PDF witness discloses its construction and binds the Wayback URL/Memento header, byte-identical original PDF and retained text. Report-level market lead time remains UNKNOWN, and the nested replay metric is labeled as a snapshot statistic.

The controller's retained gate reports 330 tests passed, one skipped, compilation, Ruff and three fixture bundles passing. Two fresh replays yielded byte-identical outputs; `FINAL-BYTE-PROOF.json` reports 61 indexed evidence/input/result files equal to working bytes. I independently ran `git diff --cached --check` and saw no errors. These checks do not resolve the buyer-path semantic overstatement. Preserve this review and request fresh review of the repaired tree.
