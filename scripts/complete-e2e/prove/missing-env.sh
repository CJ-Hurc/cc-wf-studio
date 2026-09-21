#!/usr/bin/env bash
# Purpose: Prove universal missing-env fail-closed for cc-wf-studio.
# Goal: product declares required runtimes (root engines.node + vscode engines.vscode).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
node <<'NODE'
const fs = require('fs');
const root = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const vs = JSON.parse(fs.readFileSync('packages/vscode/package.json', 'utf8'));
if (!root.engines || !root.engines.node) {
  console.error('missing root engines.node');
  process.exit(1);
}
if (!vs.engines || !vs.engines.vscode) {
  console.error('missing packages/vscode engines.vscode');
  process.exit(1);
}
console.log(
  'complete-e2e prove missing-env: engines.node=',
  root.engines.node,
  'engines.vscode=',
  vs.engines.vscode
);
NODE
exit 0
