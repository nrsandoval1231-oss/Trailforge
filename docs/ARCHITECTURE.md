# TrailForge Architecture

## Smallest useful system

`Project Timeline -> TemporalWorld -> Signal Policy -> FrozenDecisionLedger -> Lead-Time Evaluator -> Experiment Store/Replay`

The architecture answers: **would this signal policy have surfaced the project earlier using only evidence available at the time?**

Project timelines retain source-backed signals and availability times. TemporalWorld prevents future leakage. Signal Policy deterministically decides whether visible evidence warrants human commercial review. FrozenDecisionLedger retains exact evidence and decisions. Lead-Time Evaluator compares first valid surface with a later verified conventional milestone. Experiment Store/Replay preserves inspectability and deterministic replay.

## Commercial boundary

`TrailForge signal -> direct customer/project team -> verify power gap -> choose generation/fuel solution`

Fuel-provider discovery must not become the upstream architecture.

## Build rule

Use the existing engine. Add only what is required to run real historical cohorts and measure lead-time advantage. Do not add databases, distributed services, agents, governance layers, or new policy frameworks unless a concrete experiment requires them.
