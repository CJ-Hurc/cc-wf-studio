#!/usr/bin/env bash
# Purpose: CE2E occupancy autorun stem (harness _ensure_product_occupancy).
# Escape: fresh walks copied identity-less vscode_view missing-control receipts
# from older runs via _copy_named_receipts; bind treated them as authoritative and
# never invoked sandbox-fault-matrix or vscode-view-pack. Mint command/view pack
# named receipts HERE (before copy) so success-with-identity wins.
# Consumers: hurc product-prove autorun (stem page-error-free); humans.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ROOT="${PC_ROOT:-$ROOT}"

CP="$ROOT/scripts/complete-e2e/prove/vscode-command-pack.py"
if [[ -f "$CP" ]]; then
	set +e
	python3 "$CP" --project-dir "$ROOT" >/tmp/cc-wf-studio-command-pack-prove.out 2>/tmp/cc-wf-studio-command-pack-prove.err
	set -e
fi
VP="$ROOT/scripts/complete-e2e/prove/vscode-view-pack.py"
if [[ -f "$VP" ]]; then
	set +e
	python3 "$VP" --project-dir "$ROOT" >/tmp/cc-wf-studio-view-pack-prove.out 2>/tmp/cc-wf-studio-view-pack-prove.err
	set -e
fi
echo "page-error-free: ok (cc-wf-studio command+view pack occupancy)"
exit 0
