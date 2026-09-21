#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# Forward to prove.py --run so bare shell wrap still executes product proofs;
# CLI-contract surface remains prove.py (bare → usage/nonzero).
exec python3 "$ROOT/scripts/complete-e2e/prove.py" --run "$@"
