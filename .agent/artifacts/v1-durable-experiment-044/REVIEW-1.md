## Slice 2 independent review: **FIX**

I reviewed the frozen diff from `15247421e00303e36436961a91096efa55194ade`, including the untracked `test_experiment.py`, against the task and owner brief. I did not read builder completion claims or rerun the controller’s full gate.

**What passes:** Decision-time inputs are captured before policy invocation and detached from mutable state. Ledger outputs preserve the policy’s actual forecast rather than regenerating an explanation during inspection. The saved input supports replay after the original file is unavailable. Ordinary JSON outcomes remain labeled unsealed and unscored. Exclusive directory creation prevents overwriting an existing experiment. The prior malformed legacy-manifest tests remain present.

### Bounded repair findings

1. **Saved config and input are insufficiently bound.** [runner.py](/C:/Users/nrsan/Nucleus/02_Projects/Trailforge/src/athena_procurement_arena/runner.py:148) verifies file hashes but does not require supported policy/config values or reconcile scenario metadata across input, config, and manifest. In an offline probe, I changed `config.json`’s scenario ID to `"wrong"` and updated its artifact and manifest hashes: both inspect verification and replay still passed. An experiment created with policy ID `"UNSUPPORTED"` also replayed as `PASS`. Validate the supported policy, version and parameters, required field types, and cross artifact identity before either command reports success. This is a format and binding requirement; it does not assume hashes resist deliberate coordinated rewriting.

2. **Source attribution needs repair.** [runner.py](/C:/Users/nrsan/Nucleus/02_Projects/Trailforge/src/athena_procurement_arena/runner.py:78) queries distribution `"trailforge"`, while the project is `"athena-trailforge"`: the probe returned `package_version=None` although the installed distribution reports `0.1.0`. It also treats any Git ancestor of the loaded package as its source repository, which can attribute an installed package beneath an unrelated repository to that repository. Resolve distribution metadata against the *loaded* package location, and report Git identity only when that repository actually owns the loaded source.

3. **Symlink safety is incomplete.** [runner.py](/C:/Users/nrsan/Nucleus/02_Projects/Trailforge/src/athena_procurement_arena/runner.py:148) resolves the experiment directory before checking `is_symlink()`, losing evidence that the supplied directory was a symlink. It reads `manifest.json` without a symlink check. The four named artifacts receive checks. Reject symlinked experiment and manifest paths before following them. Windows permissions prevented a live symlink probe; this finding follows from the read path.

4. **The separate evaluation omits the later declared information.** [runner.py](/C:/Users/nrsan/Nucleus/02_Projects/Trailforge/src/athena_procurement_arena/runner.py:122) saves counts and a sentence pointing back to input truth, but does not identify the declared truth or later evidence in the separate evaluation artifact. Retain those values there with explicit unverified/unsealed labels, while keeping them out of earlier decision snapshots and leaving outcome metrics unscored.

5. **Required tests do not yet prove several named behaviors.** [test_experiment.py](/C:/Users/nrsan/Nucleus/02_Projects/Trailforge/tests/procurement_arena/test_experiment.py:78) has no future review attestation, never mutates policy input to test detachment, and asserts that an unused empty list remains empty. [test_cli.py](/C:/Users/nrsan/Nucleus/02_Projects/Trailforge/tests/procurement_arena/test_cli.py:42) exercises inspect in the same process. Add focused assertions for persisted future-reviewed annotations, mutation detachment, unsupported/malformed config, cross bindings, and source attribution. The controller’s reported fresh-process, tamper, repeat, and wheel acceptance runs cover some other gaps; I have not treated those runs as failed.

6. **`inspect` is machine-readable but difficult to read as documented.** [cli.py](/C:/Users/nrsan/Nucleus/02_Projects/Trailforge/src/athena_procurement_arena/cli.py:188) prints one compact JSON line containing the full input text and all nested artifacts. [README.md](/C:/Users/nrsan/Nucleus/02_Projects/Trailforge/README.md:47) promises a readable inspection path. Provide a readable ordered view, or adjust the documented workflow to show how to obtain one, while retaining machine-readable output.

No finding requires **ESCALATE**. The offline probes used fresh temporary directories and made no source edits. I accept the controller’s reported 197-test/full-gate and acceptance results as reported evidence, but these findings prevent an independent **PASS** for this exact Slice 2 candidate. This is not a review of full V1 acceptance.

### Exact six-file candidate hashes (SHA-256)

| File | Hash |
|---|---|
| `README.md` | `408834F9EF4267E48E75B468DA18C079045A5631CC214F478B74884A97C48805` |
| `src/athena_procurement_arena/cli.py` | `9EF30F1553D573ACB057C47A86C9AA6057B125B0C894C017F85C1170834BF04B` |
| `src/athena_procurement_arena/runner.py` | `E3A71019BE9E097DB5876703619687CD5977FE73BCD83FAA239C0D6687EFA487` |
| `src/athena_procurement_arena/world.py` | `415349B228998C6A46D2A75332A3D35438B7125676A81102AC85BF1193C35036` |
| `tests/procurement_arena/test_cli.py` | `709658EEF19AB662769B0DD1F3278BE90E467637582F923927A08F6B1B51907C` |
| `tests/procurement_arena/test_experiment.py` | `8243697079EB013B0D9F396CD2FA884655FE7378420538C0DF6FA440C2E2C1A0` |