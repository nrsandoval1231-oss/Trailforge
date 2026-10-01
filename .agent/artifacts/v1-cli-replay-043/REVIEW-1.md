**FIX** for the bounded CLI replay repair against `c216b5efbc1daeae5e62f28276f5d35f3d7b04c9`.

[cli.py](/C:/Users/nrsan/Nucleus/02_Projects/Trailforge/src/athena_procurement_arena/cli.py:205) calls `load_manifest`, whose `.pop()` operation assumes the JSON root is an object. A manifest containing `null` or a string raises an uncaught `AttributeError` instead of emitting the required machine-readable `FAIL` and returning nonzero. Add a regression test in [test_cli.py](/C:/Users/nrsan/Nucleus/02_Projects/Trailforge/tests/procurement_arena/test_cli.py) for non-object manifests.

My isolated, offline probe confirmed that changed scenarios, tampered manifests, unsupported policy/config, and false or missing saved ledger results return nonzero. An overwrite attempt preserved the existing file’s bytes. I did not rerun the controller’s reported full gate of 185 tests, compile, Ruff, and three fixture checks. The source-tree identity limitation remains deferred to Slice 2.

| File | SHA-256 |
|---|---|
| `.gitignore` | `5A78842C709794AC8D7993954676852BCD68BFF994E293C2126AD0ADB2876719` |
| `README.md` | `419D80CAFE50F2E3B5FB2EAB344F475DB490A75F04967BCFE2D932CE0FDB0E9F` |
| `src/athena_procurement_arena/cli.py` | `6603F2A72D8EDE6A5F5E7E6B5CA6D44A0AEA831397CD7B7ED3489D71BAEE33E4` |
| `tests/procurement_arena/test_cli.py` | `097DEBF5218954BE3B311A255C0165438BEFD4D9332ACA4A3641389AA2A581DA` |

No files or Git state were changed.

