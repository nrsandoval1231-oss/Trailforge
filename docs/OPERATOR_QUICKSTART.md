# Customer-first local project desk

Run from the Trailforge checkout:

```powershell
uv run --python 3.11 trailforge-operator --data .trailforge-operator.sqlite3
```

If `uv run` reports that it cannot replace a running project executable, keep
that process open and start the operator from a second PowerShell window without
syncing the environment:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
.\.venv\Scripts\python.exe -m athena_procurement_arena.operator --data .trailforge-operator.sqlite3
```

Open the loopback URL printed in the terminal. Project files persist in the
SQLite database and can be reopened after restarting the process. Use a private
local folder for the database; SQLite WAL and shared-memory sidecars are created
beside it. The default database and sidecars are excluded from Git.

Create a file as soon as a real project appears. A public source excerpt and
operator-observed time can be retained before the power need, quantity, fuel,
RFP, or buyer is known. Mark a claim REVIEWED only after entering its exact
excerpt and named reviewer. Reviewed scope and buyer claims also require a
traceable HTTP or HTTPS source URL with a hostname; those claims without a URL are rejected;
gate evaluation also leaves them UNKNOWN. Other claims marked UNKNOWN stay out
of the verified need state. A supported scope is an explicit reviewed scope value of `temporary
power`, `bridge power`, or `commissioning power`. Conflicting claims or an
explicit contradiction return the corresponding claim to unresolved. Add
correction evidence as a new record; saved evidence and interactions are
append-only. In the correction selector, link the new record to the earlier
same-claim evidence it supersedes. The earlier record remains in the dossier.

Organizations and people are separate project links with an evidence reference.
An organization role alone does not establish a budget owner or buyer. Buyer is
shown as known only when a person is explicitly marked BUYER and linked to a
reviewed buyer claim. Prepare a first-conversation brief in the dossier, then
log a conversation only after it actually happens. Drafts remain local and the
desk has no send operation.

Fuel coordination stays blocked until the project has a reviewed temporary,
bridge, or commissioning scope and a logged conversation linked to a person
whose BUYER role has its own reviewed evidence. That conversation must record a
positive MW quantity, timing, duration, and site constraints with requirements
marked understood. A later correction or contradiction relocks the gate.
Fuel fields are downstream coordination notes, not a signal to contact a
supplier.

Export a dossier with its project-level JSON link. The database schema is
versioned; unsupported versions and unreadable records produce explicit errors.
The desk's on-demand discovery checks exactly two feeds: Microsoft Local and
QTS News. Select **Check feeds now** to fetch them; the inbox retains candidates,
source dates and local first-seen times, feed errors, and excluded off-host link
counts. Review each item and use **Create project** to admit a candidate. The
new project keeps need, supply, timing, and buyer UNKNOWN until separately
verified. Dismissal can be reversed. Discovery does not crawl articles or run in
the background.

This is a single-operator local tool, not a CRM, broad source crawler, forecast, or
outreach system. The two-feed coverage is deliberately narrow. Real-source intake does not prove a customer relationship,
buying intent, competitive lead time, or forecast accuracy.
