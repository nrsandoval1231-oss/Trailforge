# Policy contract

Policies implement `observe`, `resolveEntities`, `updateTrail`,
`detectPatterns`, `forecastProcurement`, `forecastPowerNeed`, `chooseResearch`,
and `recommendAction`. `PolicyContract.run` composes those methods into a
forecast/action pair accepted by `TemporalWorld`.

`BASELINE_A` is a deterministic incumbent, not a production algorithm. The
keyword, static-score, latest-event, buyer-frequency, and seeded-random
controls are comparison baselines.
