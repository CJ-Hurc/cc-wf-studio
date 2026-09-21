#!/usr/bin/env bash
# Purpose: Prove capability:repository cleanup for cc-wf-studio monorepo.
# Goal: build/install artifacts are gitignored (no state leak after prove).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
test -f "$ROOT/.gitignore"
grep -qE '^node_modules/?$' "$ROOT/.gitignore"
grep -qE '^out/?$' "$ROOT/.gitignore"
grep -qE '^dist/?$' "$ROOT/.gitignore"
grep -q '\.vsix' "$ROOT/.gitignore"
echo "complete-e2e prove cleanup: node_modules/out/dist/vsix ignored ok"
exit 0
