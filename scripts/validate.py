"""Run the complete local Trailforge gate on any platform.

This is the single implementation of the gate; `scripts/validate.ps1` and the
GitHub Actions workflow run the same steps so local and remote results agree.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLE_DIR = ROOT / "scenarios" / "fixtures" / "verified"


def _tool(module: str, *args: str) -> list[str] | None:
    """Prefer the current interpreter's module, else the tool on PATH."""
    if importlib.util.find_spec(module) is not None:
        return [sys.executable, "-m", module, *args]
    executable = shutil.which(module)
    return [executable, *args] if executable else None


def _steps() -> list[tuple[str, list[str]]]:
    steps: list[tuple[str, list[str]]] = []
    for name, module, args in (
        ("test suite", "pytest", ("-q",)),
        ("ruff", "ruff", ("check", "src", "tests", "scripts")),
    ):
        command = _tool(module, *args)
        if command is None:
            raise SystemExit(f"{module} is not installed; run: pip install -e \".[dev]\"")
        steps.append((name, command))
    steps.insert(1, ("compile source", [sys.executable, "-m", "compileall", "-q", "src"]))
    for bundle in sorted(BUNDLE_DIR.glob("*.json")):
        steps.append((
            f"validate bundle {bundle.name}",
            [sys.executable, "-m", "athena_procurement_arena", "validate-bundle",
             "--bundle", str(bundle)],
        ))
    return steps


def main() -> int:
    env_note = "" if (ROOT / "pyproject.toml").exists() else " (run from the repository root)"
    for name, command in _steps():
        print(f"==> {name}{env_note}", flush=True)
        completed = subprocess.run(command, cwd=ROOT)
        if completed.returncode != 0:
            print(f"Validation failed at: {name}", file=sys.stderr)
            return completed.returncode
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
