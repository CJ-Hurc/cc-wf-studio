#!/usr/bin/env python3
"""Emit runtime surfaces with kinds registered in hurc KIND_PACKS.

Escape: ce2e-20260921T152450Z-46181 minted MISSING_PACK:3 when this adapter
emitted capability:{repository,vscode-extension,filesystem} with kinds absent
from KIND_PACKS (unknown-surface-kind). Capability grain for repository
universal is synthesized by the harness compiler; do not re-emit it here.
Nested packages/vscode contributes are harvested explicitly (root package.json
has no engines.vscode).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict:
	try:
		data = json.loads(path.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError):
		return {}
	return data if isinstance(data, dict) else {}


def _surfaces() -> list[dict[str, object]]:
	out: list[dict[str, object]] = []
	prove = ROOT / "scripts" / "complete-e2e" / "prove.py"
	if prove.is_file():
		out.append(
			{
				"id": "cli:prove",
				"kind": "cli",
				"path": "scripts/complete-e2e/prove.py",
				"package_dir": ".",
				"origin": "runtime",
				"discovered": True,
				"behavior_proven": False,
			}
		)

	# Monorepo VS Code extension leaf (root package.json is not an extension).
	ext_pkg_path = ROOT / "packages" / "vscode" / "package.json"
	ext_pkg = _load_json(ext_pkg_path)
	contrib = ext_pkg.get("contributes") if isinstance(ext_pkg.get("contributes"), dict) else {}
	rel_pkg = "packages/vscode/package.json"
	for cmd in contrib.get("commands") or []:
		if not isinstance(cmd, dict) or not cmd.get("command"):
			continue
		cid = str(cmd["command"])
		out.append(
			{
				"id": f"vscode:command:{cid}",
				"kind": "vscode_command",
				"path": rel_pkg,
				"package_dir": "packages/vscode",
				"origin": "runtime",
				"discovered": True,
				"behavior_proven": False,
			}
		)
	views = contrib.get("views")
	if isinstance(views, dict):
		for _group, items in views.items():
			if not isinstance(items, list):
				continue
			for item in items:
				view_id = item.get("id") if isinstance(item, dict) else None
				if not isinstance(view_id, str) or not view_id.strip():
					continue
				out.append(
					{
						"id": f"vscode:view:{view_id}",
						"kind": "vscode_view",
						"path": rel_pkg,
						"package_dir": "packages/vscode",
						"origin": "runtime",
						"discovered": True,
						"behavior_proven": False,
					}
				)
	return out


def main() -> int:
	payload = {
		"schema": "hurc-complete-e2e-runtime-surfaces/v1",
		"project": str(ROOT),
		"surfaces": _surfaces(),
	}
	print(json.dumps(payload, indent=2))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
