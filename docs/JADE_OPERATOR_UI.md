# Jade operator UI

The operator desk now follows the approved Jade preview: a graphite project navigation rail, quiet utility strip, editorial project heading, dark jade glass next action, and uncluttered project queue. Its screens use the existing operator APIs and SQLite records.

The project desk lists real saved records and provides manual intake, search, and a next action based on the current server response. Project files retain the complete project document, including source dates, observed dates, exact excerpts, reviewer, organizations, people, draft brief, interactions, and fuel fields. Evidence, organizations, people, and interactions already present in the server history render read-only. New records append; a correction links to earlier same-claim evidence.

Discover checks the two configured official feeds, Microsoft Local and QTS News, only after the operator presses **Check feeds now**. Candidates remain pending review until admitted or dismissed. Feed failures, last-success time, excluded off-host links, and empty results are shown as returned by the API.

Buyer research and Conversations select a saved project and render its actual records. Conversation preparation remains a draft; interaction logging requires the operator to enter what happened. No message-sending API is present. Fuel controls are enabled only when the saved project response reports `gate.fuel_unlocked`; saving newly appended evidence resets fuel coordination to `NOT_STARTED`, matching the existing operator behavior.

All mutations submit the complete project document and increment its version. On stale-version rejection, the editor keeps its draft visible and offers a JSON download and explicit server reload. Export remains the existing `/api/projects/{id}/export` endpoint. Discovery admission, dismissal, session token, and project CRUD keep their existing routes and authentication.

The assets contain no inline scripts, inline styles, event-handler attributes, HTML string injection, or external font imports. DOM content is written with text nodes; source links use the discovery response URL and open with `noopener noreferrer`. The Research Arena link is visually separated and points to its distinct local port, `127.0.0.1:8765`.

`node --check src/athena_procurement_arena/operator_assets/app.js` passed. Full validation against the isolated synthetic database, browser sizes and real-data rendering are assigned to the controller; this builder did not mutate the owner database, start the user's server, or run the repository-wide suite.
