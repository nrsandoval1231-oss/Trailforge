# LOCAL-UI-047 repair 1 — builder handoff, unaccepted

Repaired the rejected-request Windows transport race within the repair packet.
Changed only `src/athena_procurement_arena/local_ui.py`,
`tests/procurement_arena/test_local_ui.py`, and `docs/LOCAL_UI.md`, plus these
new REPAIR-1 handoff files. Original COMPLETION.json, BUILDER-HANDOFF.md and
CANDIDATE-1-VALIDATION.md remain unchanged. Hashes are in
REPAIR-1-COMPLETION.json. Branch/base remain `codex/trailforge-local-ui` /
`3cedc8711ceec0ac411f04911fa24186a0d6ceb1`.

## Diagnosis before repair

The original focused `-k request_guards` run passed (12 passed, 39 deselected,
6.30s); this is consistent with a scheduling race and does not negate the
controller's failed full gate. Python 3.11 local stdlib inspection showed
`HTTPConnection._send_output` sends headers and body in separate sends, while
`TCPServer.shutdown_request` immediately half-closes and closes the socket.
The UI rejects Transfer-Encoding before reading the body. Windows can abort
the connection if the separate body send arrives after that close, preventing
the client from reading the already-issued 400 response.

Controlled probes established the boundary: body queued before close returned
HTTP400 in two 30-request probes. Body sent after server shutdown completed
produced **ConnectionAbortedError WinError10053 in 30/30 requests**. These were
diagnostic failures, never counted as pass. The first ad-hoc probe invocation
omitted `--with pytest` and failed at importing the test helper; adding that
dependency allowed transport diagnosis. No implementation was changed then.

Added a controlled regression to the allowed test file before fixing the
server. It waits for the rejection reply, introduces a deliberate 20ms
header/body scheduling gap, sends the complete small body and requires the
explicit HTTP status and JSON error body. All four parameterizations failed
against candidate1 at `http.client.getresponse()` / `socket.recv_into()`:

```text
ConnectionAbortedError: [WinError 10053] An established connection was aborted
by the software in your host machine
4 failed, 51 deselected in 2.47s
```

Cases: properly chunk-framed body (400); raw body with Transfer-Encoding as
in the original failing helper (400); Transfer-Encoding plus Content-Length
(400); rejected text/plain body (415). The baseline command was:

`uv run --python 3.11 --with pytest --with ruff pytest -q tests/procurement_arena/test_local_ui.py -k rejection_delayed_body_transport`

It exited 1. Existing helpers, assertions and skips were not relaxed.

## Bounded change

Override `WorkbenchServer.shutdown_request` to half-close output after the
response, then discard raw socket bytes up to **5120 bytes** and an absolute
**250ms monotonic deadline**, stopping earlier at peer EOF or socket error.
Always close the socket in `finally`. This cleanup occurs after the handler
returns, outside its root-operation lock. It never parses rejected framing,
trusts Content-Length, executes policy, dispatches another request, or changes
Host/Origin/token/content-type/schema rejection. Transport cleanup catches
disconnect/timeout only; test clients still fail on any transport error.

Added deterministic fake-transport checks for byte exhaustion, absolute deadline
despite progressing reads, timeout and EOF. All require socket closure. The
real controlled sender repeats each scenario ten times without retries; every
request must receive its exact expected HTTP status and JSON error response.
Documentation explains cleanup bounds and the remaining disconnect limitation
for peers sending beyond those bounds.

## Repaired-candidate checks

- Combined original guards/new regressions: `uv run --python 3.11 --with pytest --with ruff pytest -q tests/procurement_arena/test_local_ui.py -k 'rejection_delayed_body_transport or transport_drain or request_guards'` — exit0, 20 passed, 39 deselected in9.39s.
- Final focused suite: `uv run --python 3.11 --with pytest --with ruff pytest -q tests/procurement_arena/test_local_ui.py` — exit0, **58 passed, 1 skipped in31.10s**. UTC18:21:57.4469981 → 18:22:29.3421361 on2026-10-01; measured wall31.8966604s.
- Fixed three additional invocations: `uv run --python 3.11 --with pytest --with ruff pytest -q tests/procurement_arena/test_local_ui.py -k 'rejection_delayed_body_transport or transport_drain'` — exits0/0/0, each8 passed/51 deselected; durations3.15s/3.17s/3.21s. **120 delayed-body requests** all produced required statuses. Loop stopped on any failure; no retry-to-green behavior. Total measured wall11.826858s, overlapping final focused suite.
- `uv run --python 3.11 --with pytest --with ruff ruff check src/athena_procurement_arena/local_ui.py tests/procurement_arena/test_local_ui.py` — exit0, all checks passed.
- Excluded runner/CLI/fixtures/policies/world and scenario fixtures: `git diff --exit-code -- src/athena_procurement_arena/runner.py src/athena_procurement_arena/cli.py src/athena_procurement_arena/fixtures.py src/athena_procurement_arena/policies.py src/athena_procurement_arena/world.py scenarios/fixtures` — exit0.

## Timing, limitations and next boundary

Repair1 first clock sample2026-10-01T18:17:23Z (after packet read); implementation
and validation finish sample18:22:32Z. Exact turn start, separate planning/build
durations, actual runtime model/config identity and tokens remain UNKNOWN.
Requested model/reasoning: gpt-6-astra/medium. Repair count1. Independent audit
and elapsed-to-accepted remain null. The pre-fix failed regression is retained
above, not erased by subsequent success.

The existing live symlink test is still skipped for missing Windows privilege;
no new skip was added. Cleanup is deliberately bounded: peers sending later
than250ms or beyond5KiB may still lose the response when disconnected. No
unbounded waiting, permissive Transfer-Encoding parsing or security downgrade
was introduced. Candidate1's controller source/wheel success is historical
evidence; its full-gate failure remains retained. The controller must rerun
final gates and review this changed candidate. No self-acceptance, delegation,
commit, push, merge or deployment occurred.
