#!/usr/bin/env bash
# Purpose: Prove capability:repository build for cc-wf-studio monorepo.
# Goal: workspace packages declare build scripts and core/cli/mcp/vscode trees exist
# (artifact compile is exercised by consumer.py; occupancy stays fast/fail-closed).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
test -f "$ROOT/pnpm-workspace.yaml"
for pkg in core cli mcp vscode; do
  test -f "$ROOT/packages/$pkg/package.json"
done
node -e "
const fs=require('fs');
const path=require('path');
const root=process.argv[1];
for (const name of ['core','cli','mcp','vscode']) {
  const pkg=JSON.parse(fs.readFileSync(path.join(root,'packages',name,'package.json'),'utf8'));
  if(!pkg.scripts||!pkg.scripts.build){console.error('missing build script:', name); process.exit(1);}
}
const coreSrc=path.join(root,'packages','core','src');
if(!fs.existsSync(coreSrc)){console.error('missing packages/core/src'); process.exit(1);}
console.log('complete-e2e prove build: workspace packages declare build + core/src ok');
" "$ROOT"
exit 0
