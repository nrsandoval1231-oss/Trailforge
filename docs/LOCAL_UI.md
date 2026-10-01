# Local experiment workbench

Launch from PowerShell in the checkout:

```powershell
Set-Location 'C:\Users\nrsan\Nucleus\02_Projects\Trailforge'
uv run --python 3.11 trailforge-ui
```

Open the printed address, normally `http://127.0.0.1:8765/`. Use that exact
host and port; `localhost` is deliberately rejected. Stop with Ctrl+C. The
default experiment root is `.trailforge-experiments` in the launch directory.
Keep that directory to retain runs; it is ignored by Git.

Choose GT-003, expand its source/reviewer context, then **Run and save**.
The optional adapter uses the existing fixture parser and BASELINE_A 1.0,
with the fixture's fixed seed. Each run receives a new opaque ID and the
runner refuses overwrite. GT-003 is a generator-maintenance negative mechanics
case, not a qualified temporary-power opportunity. South Valley is not admitted.
Only GT-003 fixture IDs in trusted startup bundles are offered by this extension.

Select a saved run to verify its artifact hashes, ledger bindings and retained
context. The evidence strip shows actual retained decision timestamps; select
a time to inspect its action, policy output/rationale, visible evidence and
ledger record. Later evidence and declared truth appear separately in unsealed
evaluation. **Verify replay** explicitly executes the existing deterministic
policy against the retained input and shows each replay check. Integrity PASS
and replay PASS are separate results; neither establishes forecast accuracy.
UNSEALED / UNSCORED, missing outcome approval, and UNKNOWN remain explicit.

Restart with the same experiment root to recover runs. Inspection and replay
do not require the original bundle:

```powershell
uv run --python 3.11 trailforge-ui --saved-only --experiments-dir .trailforge-experiments
```

Replay results are session-local, bound to the verified manifest, and reset to
NOT_RUN after restart. Inspection/replay never rewrite the saved run artifacts.
Corrupt or partial UUID-named runs remain listed with integrity FAIL; replay
is blocked until their retained data can be verified. Keep failed runs for
investigation. A new run does not repair, overwrite or certify an old run.

For an installed wheel or a different trusted root, supply paths at startup:

```powershell
trailforge-ui --bundle C:\research\gt-003-morgan-hill.json --experiments-dir C:\research\experiments --port 8766
```

`--bundle` is repeatable. The bundle bytes are read once at startup and retained
exactly in each created experiment using the same context shape as the CLI.
The checkout default is unavailable in a normal wheel installation; missing
bundles produce a startup error. `--saved-only` is the explicit alternative.
`--port 0` requests an available local port and prints it.

## Local boundary

The server binds only 127.0.0.1. Requests require its exact Host; foreign and
null Origins are rejected. Run/replay require JSON POST, a bounded strict body,
and a random startup token compared in constant time. GET is read-only. Assets
have an exact allowlist; browser input cannot name paths or commands. Responses
use a restrictive CSP, no-store and no-referrer. Retained text is rendered with
DOM text nodes. No external assets, services or browser launch are used.

Connection cleanup half-closes output after the response, then discards at most
5 KiB of trailing bytes for at most 250 ms. This avoids a Windows reset when a
small rejected body arrives after its headers. Rejected transfer framing is
never parsed or executed. Bodies arriving beyond these cleanup bounds may still
lose the response on disconnect; cleanup does not wait indefinitely for a peer.

An OS lock permits one UI process per experiment root, and a server lock
serializes root operations. Symlinks and Windows reparse points are rejected.
Trusted local users and CLI processes can still change files; hashes detect
corruption, not deliberate coordinated forgery. The UI does not sandbox other
same-user processes. Do not expose or reverse-proxy it to a network. Large
local runs are inspected synchronously; this bounded workbench has no job queue,
pagination, case authoring, sealing, scoring, promotion or execution authority.

## Focused checks

```powershell
uv run --python 3.11 --with pytest --with ruff pytest -q tests/procurement_arena/test_local_ui.py
uv run --python 3.11 --with pytest --with ruff ruff check src/athena_procurement_arena/local_ui.py tests/procurement_arena/test_local_ui.py
```

Controller full gates, installed-wheel/browser proof and independent review
are separate from the builder's focused evidence.
