# Controller pre-freeze failure evidence — 2026-10-01 (pre-freeze)

The first discovery handoff passed 20 focused tests but had a missing adversarial
encoding case. Direct parse_feed with BOM-less UTF-16 LE/BE DTD and &e; title
returned EXPANDED for both. UTF-32 LE raised ParseError. This violates the DTD
rejection boundary despite the existing BOM-marked UTF-16 regression passing.
Do not call the first handoff accepted. Issued DISCOVER-049-R1 with exact payload
class, NUL rejection requirement and tests; preserve original COMPLETION.json.

First live app transport fetch: Microsoft 81,690 bytes; 12 fetched, 7 eligible,
5 off-host excluded. QTS returned HTTP403. Earlier source verification used a
different HTTP client and got200; never substitute that success for this app's
actual behavior. An honest identifying User-Agent may correct absent-client
metadata; do not bypass access denial. Retain source errors if it still fails.

Reviewed timeout claim: socket timeout is per operation; without an elapsed
budget it does not prove ten seconds overall. Repair must enforce an elapsed
budget or explicitly retain this as an unresolved acceptance limitation.

Controller proof-script-only failure: SQLite connection context manager did not
close its handle, causing Windows temporary-directory cleanup failure. Added an
explicit close; source application was unaffected. Rerun passed12 runtime checks.

