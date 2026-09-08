#!/usr/bin/env python3
"""cc-wf-studio complete-e2e prove wrapper — vitest/CLI/validate — no PHPUnit."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def main() -> int:
    a = set(sys.argv[1:])
    if a & {"-h", "--help"}:
        print("cc-wf-studio-prove: wraps scripts/complete-e2e/run.py live product proofs")
        return 0
    if a & {"-V", "--version"}:
        print("cc-wf-studio-prove 1.0.0")
        return 0
    return subprocess.call([sys.executable, str(ROOT / "scripts/complete-e2e/run.py")], cwd=str(ROOT))

if __name__ == "__main__":
    raise SystemExit(main())
