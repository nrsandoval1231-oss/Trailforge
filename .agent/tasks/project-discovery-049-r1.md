# DISCOVER-049-R1 — bounded pre-freeze parser and transport repair

Same repository/branch/base as DISCOVER-049. Ownership only discovery.py,
tests/test_discovery.py and new repair evidence under project-discovery-049/repair-01.
Do not alter prior COMPLETION.json. Preserve other work. No remote actions.

Controller reproduced: UTF-16 LE and BE without BOM decode as UTF-8 containing
NUL; ElementTree then detects encoding and expands a DTD entity despite byte/text
scanner. Reject NUL/non-UTF8 XML deterministically before parse; test no-BOM
UTF-16 LE/BE DTD payloads, plus normal feeds. This is actual security-boundary failure.

Live fetch through current transport: Microsoft succeeds 7 eligible / 5 excluded /
12 fetched. QTS returns HTTP403. Add honest identifying User-Agent TrailForge/0.1
(public project research), standard Accept header already present; do not bypass
an access denial, use cookies or browser fingerprints. Failure must remain visible
if service continues to deny. No retries against blocked access controls.

Current socket timeout is per operation, not an absolute source deadline. Implement
bounded overall fetch deadline (including DNS wait) or correct the explicit
contract claim and surface timeout reliably. Prefer one bounded total deadline,
pinned public addresses, default TLS, bounded read loop and clean resource closure.
Do not introduce asynchronous background polling or uncontrolled threads.

Run focused discovery/operator tests, Ruff/compile/JS check only if changed. Handoff
new exact file hashes and actual outcomes; full gate and independent review remain
controller-owned. This is first post-handoff repair attempt. Return concrete blocker
if a strict total DNS bound cannot be safely implemented within this packet.
