# Policy contract

`PolicyContract` defines `observe`, `resolveEntities`, `updateTrail`,
`detectPatterns`, `forecastProcurement`, `forecastPowerNeed`, `chooseResearch`,
and `recommendAction`. `PolicyContract.run` composes those methods into a
forecast/action pair. `TemporalWorld` invokes whatever callable it is given
and expects that pair.

Only `BaselineA` implements `PolicyContract`. It is a deterministic incumbent,
not a production algorithm. The keyword, static-score, latest-event,
buyer-frequency, and seeded-random controls are plain callables that return
the same forecast/action tuple. They are comparison baselines and do not
implement the eight contract methods.
