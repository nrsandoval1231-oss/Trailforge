# TrailForge historical signal workbench

The workbench is a local research instrument for retaining project evidence and comparing bounded early signals with later procurement milestones. It starts empty, performs no acquisition, and makes no claim of predictive or commercial success.

## Run and verify

Use Node.js 22. There are no dependencies, installation steps, build steps, credentials, CDN resources, or runtime network acquisition.

From the repository root:

```sh
node workbench/server.mjs
```

Open the loopback URL printed by the server, normally `http://127.0.0.1:3000`.

Run the scaffolded acceptance tests from the repository root:

```sh
node --test
```

The scaffolded `package.json` is at the repository root. If npm is available, these equivalent repository-root commands are optional conveniences; no install is necessary:

```sh
npm start
npm test
```

The HTTP server binds to `127.0.0.1`. Override its port and storage directory with `PORT` and `DATA_DIR`. For example, on a POSIX shell:

```sh
PORT=3100 DATA_DIR=/absolute/writable/trailforge-data node workbench/server.mjs
```

Defaults are port `3000` and `./data`, resolved from the process working directory. For a read-only source deployment, choose a writable external directory using `DATA_DIR`. Persistent application state is stored in `DATA_DIR/workbench.json`; temporary atomic replacement files also remain in that directory. Static assets are resolved relative to the server module rather than the working directory.

## Operator workflow

1. Create a project with its name, location, and research notes. Saving opens the project detail. Hash routes retain the current view after reload.
2. Search the project collection by a literal substring of its name, location, or notes. Include archived projects without clearing the search. Archive requires a named confirmation dialog; Cancel and Escape leave the project unchanged. Restore brings a retained project back into the active collection.
3. Append evidence using a public HTTP(S) source reference, exact excerpt, and exact contiguous quote. The excerpt is retained without whitespace normalization and hashed from its UTF-8 bytes. Evidence cannot be edited or deleted.
4. Enter a supported SignalType value exactly as defined in the preserved signal ledger. The signal-type input accepts all existing ledger values; types in the project's imported references and existing evidence appear as suggestions. `PROCUREMENT_SIGNAL` is the comparison target and never a policy input.
5. Keep event, document, and historical availability clocks separate. Unknown clocks remain unknown. The default availability status is `UNREVIEWED`.
6. Run a single-project review from project detail, or select 1–50 active projects in the collection and name a cohort report. Search filtering does not discard selected projects. The report freezes their current snapshots.
7. Inspect per-case status, first investigation time, comparison availability, signed lead, buyer organizations, and unresolved counts. Select a decision-time button to inspect only the retained evidence visible at that time. Procurement context is shown separately, outside the decision panel.
8. Use **Verify replay** to explicitly recompute the retained inputs. A successful replay displays **Replay matched**. Integrity and replay are separate checks. Failed integrity withholds healthy result cards and export.

## Revisions and recoverable failures

Project changes and evidence appends require the current project revision. A stale request returns `409` and commits no changes. Failed metadata saves display **Could not save project** and retain every editor value for manual retry. On a revision conflict, load the current revision explicitly; the editor shows the current stored metadata without replacing your entered values. Review the differences before saving again. Another concurrent write can still cause a further conflict.

Evidence append conflicts likewise retain the intake values and offer an explicit revision refresh. Import errors retain the pasted JSON and project fields. Persistence errors remain visible rather than presenting an unsuccessful operation as saved. Avoid retrying a request blindly if its response was lost: reload or inspect the collection first to determine whether the server committed it.

## Availability and baseline limits

`ATTESTED` availability requires all three timestamps, a reviewer, proof URL, and explanation. Timestamps must be timezone-aware ISO instants no later than the operation time. Event and document times cannot follow availability. The UI labels attestation as an operator assertion. A reviewer name, URL, or supplied hash is not independent authentication, and URLs are never fetched.

The bounded `PRE_RFP_BASELINE_V1` uses only attested non-target evidence available at each decision time. Any visible record explicitly supporting generation not in scope, an award, or resolved supply suppresses. Otherwise investigation requires one record supporting project identity, generation need, a known need reason, and a known buyer organization. Unsupported claims remain unspecified; blank or `UNKNOWN` text does not establish a known reason or buyer. Otherwise the decision is WATCH.

Historical lead equals comparison availability minus first investigation time, in days. Negative values are retained. Missing surfaces and milestones remain unresolved. Coverage is matched cases divided by cases with an attested comparison target, or unresolved when there are no targets. The median uses the lower middle measured lead. Decision count describes retained action burden, not commercial effectiveness.

## Trace imports

Use **Import trace JSON** to paste an existing `trailforge-project-trace-v1` public trace. Valid imports preserve the entire original JSON as `NOT_AUTHENTICATED` reference context. Imported signals are labeled **Imported reference — availability unreviewed**. Their observation dates, quotes, and supplied hashes do not create captured excerpts, attested availability, or baseline inputs. Add separately supported evidence through the normal append form when historical proof is available. Imports do not run or replace the Python research system.

## Retention, backup, and export

Projects and reports survive reload and server restart when the same `DATA_DIR` is used. Archiving retains evidence and frozen report references. Later metadata edits, evidence additions, and archiving do not rewrite frozen reports. Reports have no edit or delete operation.

For a complete backup, stop the server cleanly and copy `DATA_DIR/workbench.json` to another location. Restore with the server stopped by placing the unchanged backup at the chosen data directory's `workbench.json`, then restart with that `DATA_DIR`. Malformed or unsupported persisted data fails on opening rather than being silently replaced.

**Export verified JSON** downloads the complete frozen report, including retained inputs, policy identity, cases, summary, and hashes. Keep the full object for independent verification and replay through the domain module's `verifyReport(report)` function. Exporting an individual report is useful for retaining research artifacts; it is not a replacement for backing up the complete project store.

## Preserved Python workflows

The Node workbench is an isolated application. It does not execute, replace, or migrate the Python Arena, research entrypoints, retained evidence, brand assets, or existing artifacts. Continue using their existing documented Python workflows. The workbench implements only the narrow documented Pre-RFP compatibility baseline and reference intake described above.

## Browser verification

With the server running, check creation and prefilled editing, then reload the same project route to confirm persistence. On a phone-sized viewport, verify that navigation and action controls wrap, dialogs remain scrollable, and the document has no horizontal overflow. Open archive confirmation and cancel with both Cancel and Escape. Simulate a recoverable save failure and confirm exact editor values remain available for retry. Append default unreviewed evidence, run a review, confirm **Historical lead unresolved**, reload the report route, and explicitly replay it. Also inspect an attested decision timeline and confirm later evidence appears only at decision times when it was available.
