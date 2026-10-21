# DISCOVER-049: On-demand official project-source discovery

Repository C:/Users/nrsan/Nucleus/02_Projects/Trailforge; branch codex/trailforge-customer-v1;
base cbb10d33c5604e0ed2a1eac668bfbee6c1cba8e7 plus frozen OPERATOR-048 handoff.
One Luna, serialized after 048. No new Tribunal; Sol approved this thin adapter.

Objective: satisfy actual project detection in the owner workflow; manual forms
alone are a partial product. Read two fixed official owner/developer news feeds
on explicit operator request, retain candidate titles/URLs/dates, and let operator
open source and admit a project with need/buyer/fuel UNKNOWN. No supplier-first path.

## Verified source configuration

- microsoft-local: https://local.microsoft.com/feed/ ; entry host local.microsoft.com
- qts-news: https://q.com/news/feed/ ; entry host q.com

Controller discovered these exact RSS URLs in official page link metadata and
successfully fetched and parsed both on 2026-10-01. Sizes approximately 82 KB and
79 KB. Microsoft includes Silver Springs datacenter construction update dated
September 28, 2026. Feed items include unrelated news: remain PENDING_REVIEW;
do not claim every item is a project or need. Off-host links must be excluded with
visible count/reason; no follow/redirect. Actual fetch failure stays visible.

## Ownership

Allowed: discovery.py, operator.py integration, operator_assets, tests/test_discovery.py,
operator tests only as needed, docs/OPERATOR_QUICKSTART.md, README, package assets
if needed, .agent/artifacts/project-discovery-049/.
Excluded: existing research engine/UI/fixtures, controller docs/graph and 048 evidence,
credentials, external sending, paid integrations, remote Git state.
Not alone: preserve all existing 048 implementation/controller work.

## Required behavior and boundaries

- Protected POST Discover now: fixed URLs only, no arbitrary URL/body target.
- HTTPS/default TLS, reject redirects, 10-second timeout/source, maximum 1 MiB
  response and 50 items/source; XML only; reject DOCTYPE/ENTITY and malformed input.
- Static host allowlist plus reject any nonpublic DNS destinations before fetch;
  no local/metadata access. Do not broaden existing public_capture.py boundary.
- Durable candidate and source-check tables with transactions, exact URL dedupe,
  title+URL snapshot hash, first_seen UTC separate from source-stated pubDate;
  never invent historical availability. Preserve older rows on source failure.
- GET inbox shows title, source URL, date (UNKNOWN if absent), first-seen and review
  state. Search candidates; dismiss irrelevant with reversible status; no score.
- Explicit Create project action: candidate title/source evidence marked UNKNOWN,
  project link saved atomically and repeated admission idempotent. Permit operator
  to edit project title/location/phase after source review. Do not auto-qualify.
- Correct HTML escaping/text rendering and safe external links; no feed HTML injected.
- Per-feed last success/error and checked time; fetched vs eligible vs dismissed
  counts honest. No background scheduler, article scraper or contact sender.
- One request can take bounded 20 seconds; UI busy and clear failure states.
- Keep operator workflow intact. Freeze integrated 048+049 before independent review.

## Proof/handoff

Focused tests using fake transport: RSS/Atom parsing, malformed/DOCTYPE/oversize,
redirect/nonpublic/off-host rejection, dedupe and first_seen preservation, partial
failure retention, restart, idempotent admission, UNKNOWN and protected request.
Do not make unit gates depend on live feeds. Controller runs live feeds and browser.
Record focused tests, file hashes, UTC start/end, measured versus UNKNOWN metrics,
COMPLETION.json. No self-certification, commit/push/merge/deploy. Two repair attempts.
