# PREVIEW-052 — Session intake integration

Sample project intake now appends a visible row to the Projects queue. The row participates in text search and filtered result counts and opens the named project detail. Its need and buyer claims remain Unknown; location and phase are shown as unknown unless supplied in the sample form. Added content is created with DOM text nodes and stays in page memory only, so refresh resets it.

Validation: `node --check` on extracted embedded JavaScript PASS; focused assertions for visible row creation, safe text rendering, filter/count update, detail identity/Unknown state, and absence of browser persistence/network APIs PASS. Controller browser validation pending.
