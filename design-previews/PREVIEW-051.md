# PREVIEW-051 — Trailforge standalone interface

Standalone, illustrative HTML concept preserving the approved “Projects worth pursuing” home hierarchy and style. Includes Projects, Discover, Conversations, Buyer research, Research Arena overview, project detail, and session-only project intake. Three color studies, responsive navigation sized for a 320px viewport, keyboard focus, pause motion, reduced-motion and reduced-transparency support are included.

All sample projects, sources, organizations and interactions are illustrative. The preview runs no searches, sends no messages, writes no backend records, and keeps form samples only in page memory. Unknown need, capacity, buyer, timing and duration stay visible; fuel coordination stays locked.

## Validation

- `node --check` on extracted embedded JavaScript — PASS (Node v24.19.0).
- Structural assertions for doctype, one main landmark, section IDs, no alert calls, three themes, reduced motion/transparency, all workspace routes, session notice, and dark mobile selected/hover states — PASS.
- Manual HTTP/browser rendering — controller reports no horizontal overflow at 390px; final controller pass pending.

Candidate SHA-256: `5723B58D3196993AAFDACFB604E51BE48992E8A735F45038A229A0F7FAE2F9FB`.
## Repair 1

The Conversations page now has a separate editable brief with visible project context and explicit unknown need, capacity and buyer fields. Questions and a draft can be edited; save retains the draft in page-session memory only. The interaction log remains a distinct form. Discover sample signals and Buyer research samples now open inline illustrative review panels with source and identity gaps stated as Unknown. Route headings use editorial descriptions.

Focused repair checks: embedded JavaScript `node --check` PASS; assertions for separate editable brief and interaction log, inline signal and buyer panels, editorial headings, and no alert calls PASS. Controller performs final browser check.

## Repair 2

Desktop navigation hover and keyboard focus now use a dark surface with readable light text. CSS assertion PASS. Frozen candidate SHA-256: CAFC75E7941EACA465327F568DE358B8C5879C6835B267F6FF3F064D0A44FD86.

## Owner-selected style — 2026-10-02

Jade is the approved default for the preview. Saved in the HTML so fresh visits and refreshes open in Jade; Copper and Arctic remain available for comparison. This style selection changes the preview candidate after prior validation; application files remain unchanged.
