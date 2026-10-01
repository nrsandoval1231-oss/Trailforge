# FC-050 runtime observations

Browser QA 2026-10-01: Chrome served the local operator snapshot at http://127.0.0.1:8758/. Desktop screenshot visibly showed one early project and one active RFP, readable cards, NOT_FIT explanation, source citations, next action and draft. ACTIVE RFPs navigation changed URL to #active. DOM inspection showed relative links to the three retained original PDFs and hashed captures. Server is loopback-only. No portal interaction, bid submission or contact occurred.

Development proof attempts retained honestly: importing an identical opportunity ID again raised FileExistsError as designed (immutable record). A revised alias-dedup probe initially failed due to a probe script using Windows default cp1252 instead of UTF-8, before it could assert results. These are not product acceptance results. Corrected final proof follows below after repair freeze.

Final repair run 2026-10-01T23:27Z: v3 LIPA plus v2 Plaza imports PASS; OPEN_AS_OF_PUBLIC_SOURCE/NOT_FIT and PRE_RFP_PROJECT/NOT_SCREENED respectively. Four distinct input IDs deduplicated into two opportunities in a temporary workspace; all 12 retained local links resolved; renderer verified hashes. Fresh input preserves unknown fuel selection and manual extraction boundaries.
