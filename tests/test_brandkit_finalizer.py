"""Locked approval evidence must survive finalization byte for byte."""
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

BRAND = Path(__file__).resolve().parents[1] / "brand/trailforge-v1"


def load_finalizer(tmp_path):
    root = tmp_path / "brand/trailforge-v1"
    shutil.copytree(BRAND, root)
    spec = importlib.util.spec_from_file_location("finalize_brandkit", root / "palette/finalize_brandkit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, root


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_finalization_preserves_locked_identity_bytes(tmp_path, newline):
    module, root = load_finalizer(tmp_path)
    identity = root / "APPROVED_IDENTITY.json"
    original = identity.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", newline)
    identity.write_bytes(original)
    for _ in range(2):
        module.main()
        assert identity.read_bytes() == original
        completion = json.loads((tmp_path / ".agent/artifacts/brand-056/COMPLETION.json").read_text())
        assert completion["approval_manifest_sha256"] == module.sha(identity)


def test_finalization_rejects_changed_locked_identity_without_writing(tmp_path):
    module, root = load_finalizer(tmp_path)
    identity = root / "APPROVED_IDENTITY.json"
    original = identity.read_bytes().replace(b'"TRAILFORGE"', b'"OTHER"')
    identity.write_bytes(original)
    with pytest.raises(SystemExit, match="locked approval manifest mismatch"):
        module.main()
    assert identity.read_bytes() == original
    assert not (tmp_path / ".agent/artifacts/brand-056/COMPLETION.json").exists()
