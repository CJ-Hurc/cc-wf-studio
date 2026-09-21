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

_HELP = """Usage: run.py [options]

cc-wf-studio complete-e2e: vitest / CLI help / validate — no PHPUnit.

options:
  -h, --help     show this help message and exit
  -V, --version  show version and exit
"""

_KNOWN = {"-h", "--help", "-V", "--version"}

if __name__ == "__main__":
    args = sys.argv[1:]
    unknown = [a for a in args if a not in _KNOWN]
    if unknown:
        print(
            f"run.py: unrecognized option or argument: {unknown[0]!r}\n"
            f"Usage: run.py [options]\n"
            f"Try 'run.py --help' for options.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    a = set(args)
    if a & {"-h", "--help"}:
        print(_HELP, end="")
        raise SystemExit(0)
    if a & {"-V", "--version"}:
        print("cc-wf-studio-complete-e2e 1.0.0")
        raise SystemExit(0)
    raise SystemExit(main())
