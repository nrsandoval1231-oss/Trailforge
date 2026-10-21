# PREVIEW-052 — Session intake integration
READY dependent PREVIEW-051 frozen cafc75e7941eaca465327f568de358b8c5879c6835b267f6ff3f064d0a44fd86.
Canonical purpose: entire illustrative preview, no backend. Constraint discovered: sessionProjects is detached from visible Projects queue; fix integration between intake and existing list.
Same repo branch/base as PREVIEW-051. Allowed only design-previews/trailforge-ui-concept.html, design-previews/PREVIEW-051.md, .agent/artifacts/preview-052/COMPLETION.json. No other edits.
Acceptance: save sample project visibly adds row and updates count; search includes it; row opens named detail with UNKNOWN claims; existing 3 sample rows and themes remain correct; refresh resets data. No external effects, no localStorage. Avoid innerHTML interpolated user content without escaping. Preserve approved styling.
Validation node --check and exact hash. Controller final browser tests. No review required for reversible standalone preview; deterministic gates. One narrow builder only; retry budget 2. Record UTC times or UNKNOWN.
