#!/usr/bin/env bash
# Purpose: Prove capability:repository startup for cc-wf-studio monorepo.
# Goal: root package.json parses with engines.node; nested vscode extension tree exists.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
test -f "$ROOT/package.json"
test -f "$ROOT/pnpm-workspace.yaml"
test -d "$ROOT/packages/vscode/src"
node -e "
const fs=require('fs');
const pkg=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));
if(!pkg.engines||!pkg.engines.node){console.error('missing engines.node'); process.exit(1);}
if(!String(pkg.name||'').includes('cc-wf-studio')){console.error('unexpected package name'); process.exit(1);}
console.log('complete-e2e prove startup: engines.node=', pkg.engines.node);
" "$ROOT/package.json"
exit 0
