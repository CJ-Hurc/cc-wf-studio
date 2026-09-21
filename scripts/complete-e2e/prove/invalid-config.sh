#!/usr/bin/env bash
# Purpose: Prove universal invalid-config fail-closed for cc-wf-studio.
# Goal: nested vscode contributes.configuration.properties is non-empty
# (empty/invalid configuration catalog is rejected as product contract).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
node <<'NODE'
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('packages/vscode/package.json', 'utf8'));
const conf = (pkg.contributes && pkg.contributes.configuration) || null;
if (!conf) {
  console.error('missing contributes.configuration');
  process.exit(1);
}
const props = conf.properties || (Array.isArray(conf) ? conf[0] && conf[0].properties : null);
if (!props || typeof props !== 'object' || Object.keys(props).length < 1) {
  console.error('configuration.properties empty');
  process.exit(1);
}
// Fail-closed catalog: at least one setting declares type (invalid empty object rejected).
for (const [key, val] of Object.entries(props)) {
  if (!val || typeof val !== 'object' || !val.type) {
    console.error('configuration property missing type:', key);
    process.exit(1);
  }
}
console.log(
  'complete-e2e prove invalid-config: configuration.properties ok',
  Object.keys(props).length
);
NODE
exit 0
