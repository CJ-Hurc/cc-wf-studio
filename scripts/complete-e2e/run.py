#!/usr/bin/env python3
"""Canonical complete-e2e entry for cc-wf-studio: vitest + CLI + validate."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

def main() -> int:
    print("cc-wf-studio complete-e2e")
    print("----------------------------------------")
    rc = 0
    consumer = HERE / "consumer.py"
    r = subprocess.run([sys.executable, str(consumer)], cwd=str(ROOT))
    if r.returncode == 0:
        print("  PASS  consumer complete-e2e", flush=True)
    else:
        print("  FAIL  consumer complete-e2e", flush=True)
        rc = 1
    print("----------------------------------------")
    print("COMPLETE_E2E: PASS" if rc == 0 else "COMPLETE_E2E: FAIL")
    return rc

if __name__ == "__main__":
    a = set(sys.argv[1:])
    if a & {"-h", "--help"}:
        print("cc-wf-studio-complete-e2e: vitest / CLI help / validate — no PHPUnit")
        raise SystemExit(0)
    if a & {"-V", "--version"}:
        print("cc-wf-studio-complete-e2e 1.0.0")
        raise SystemExit(0)
    raise SystemExit(main())
