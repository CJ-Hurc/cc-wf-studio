#!/usr/bin/env python3
"""cc-wf-studio complete-e2e prove wrapper — vitest/CLI/validate — no PHPUnit."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_HELP = """Usage: prove.py [options]

cc-wf-studio complete-e2e prove wrapper (vitest / CLI / validate — no PHPUnit).

options:
  -h, --help     show this help message and exit
  -V, --version  show version and exit

With no options, runs scripts/complete-e2e/run.py live product proofs.
"""

_KNOWN = {"-h", "--help", "-V", "--version"}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    unknown = [a for a in args if a not in _KNOWN]
    # Reject unknown / malformed flags with a diagnostic (cli-contract negatives).
    if unknown:
        bad = unknown[0]
        print(
            f"prove.py: unrecognized option or argument: {bad!r}\n"
            f"Usage: prove.py [options]\n"
            f"Try 'prove.py --help' for options.",
            file=sys.stderr,
        )
        return 2
    if set(args) & {"-h", "--help"}:
        print(_HELP, end="")
        return 0
    if set(args) & {"-V", "--version"}:
        print("cc-wf-studio-prove 1.0.0")
        return 0
    return subprocess.call(
        [sys.executable, str(ROOT / "scripts/complete-e2e/run.py")],
        cwd=str(ROOT),
    )


if __name__ == "__main__":
    raise SystemExit(main())
