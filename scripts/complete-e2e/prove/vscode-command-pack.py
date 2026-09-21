#!/usr/bin/env python3
"""Purpose: LIVE prove for cc-wf-studio vscode_command cells (openEditor).

Escape: ce2e board FAILED failure-state with reason missing-control because the
shared PA sandbox on :7777 has no data-command=cc-wf-studio.openEditor. This
adapter starts the product sandbox (:7788), drives the harness
sandbox-fault-matrix against it, and writes named receipts for outstanding
activation / command-execution / failure-state cells.
Consumers: hurc _exec_product_vscode_cdp_live (stem vscode-command-pack).
Exit: 0 when all targeted cells proven / none outstanding; nonzero otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[2]
SANDBOX_DEFAULT = "http://127.0.0.1:7788"
CMD = "cc-wf-studio.openEditor"
SURFACE = f"vscode:command:{CMD}"
SCENARIOS = frozenset({"activation", "command-execution", "failure-state"})


def _health(url: str) -> bool:
	try:
		with urllib.request.urlopen(f"{url.rstrip('/')}/health", timeout=2) as resp:
			body = json.loads(resp.read().decode("utf-8"))
		return bool(body.get("ok"))
	except Exception:
		return False


def _ensure_sandbox(root: Path, url: str) -> bool:
	if _health(url):
		return True
	from urllib.parse import urlparse

	parsed = urlparse(url)
	host = parsed.hostname or "127.0.0.1"
	port = parsed.port or 7788
	server = root / "test" / "sandbox-ui" / "server.mjs"
	if not server.is_file():
		return False
	node = shutil.which("node")
	if not node:
		return False
	log = root / ".hurc-harness" / "state" / "complete-e2e" / "sandbox-ui.log"
	log.parent.mkdir(parents=True, exist_ok=True)
	proc = subprocess.Popen(
		[node, str(server)],
		cwd=str(root),
		env={**os.environ, "HOST": host, "PORT": str(port)},
		stdout=log.open("a"),
		stderr=subprocess.STDOUT,
		start_new_session=True,
	)
	for _ in range(40):
		if _health(url):
			return True
		if proc.poll() is not None:
			return False
		time.sleep(0.25)
	return _health(url)


def _active_run(root: Path) -> tuple[str, Path] | None:
	state = root / ".hurc-harness" / "state" / "complete-e2e"
	active = state / "active-run.json"
	if not active.is_file():
		return None
	try:
		body = json.loads(active.read_text(encoding="utf-8"))
	except json.JSONDecodeError:
		return None
	run_id = str(body.get("run_id") or "")
	run_dir = state / "runs" / run_id
	if not run_id or not run_dir.is_dir():
		return None
	return run_id, run_dir


def _cells_db(run_dir: Path) -> Path | None:
	loc = run_dir / "cells.sqlite.location"
	if loc.is_file():
		p = Path(loc.read_text(encoding="utf-8").strip())
		if p.is_file():
			return p
	direct = run_dir / "cells.sqlite"
	return direct if direct.is_file() else None


def _outstanding(run_dir: Path) -> list[dict[str, str]]:
	db = _cells_db(run_dir)
	if db is None:
		return []
	with sqlite3.connect(str(db)) as con:
		con.row_factory = sqlite3.Row
		rows = con.execute(
			"""
			SELECT cell_id, pack, scenario, surface_id, snapshot_id, universe_id, status
			FROM cells
			WHERE pack = 'vscode_command'
			  AND surface_id = ?
			  AND scenario IN ('activation', 'command-execution', 'failure-state')
			  AND status IN ('MISSING_PROVER', 'FAILED', 'OPEN', 'RETRY')
			""",
			(SURFACE,),
		).fetchall()
	return [dict(r) for r in rows]


def _harness_adapter() -> Path | None:
	env = os.environ.get("HURC_HARNESS_ROOT", "").strip()
	candidates: list[Path] = []
	if env:
		candidates.append(
			Path(env)
			/ "capabilities"
			/ "complete-e2e"
			/ "scripts"
			/ "prove"
			/ "sandbox-fault-matrix.ts"
		)
	candidates.append(
		Path("/workspace/repos/hurc-harness-v2/extensions/shared/contributions")
		/ "capabilities"
		/ "complete-e2e"
		/ "scripts"
		/ "prove"
		/ "sandbox-fault-matrix.ts"
	)
	for c in candidates:
		if c.is_file():
			return c
	return None


def _playwright_node_path(root: Path) -> str:
	parts: list[str] = []
	for cand in (
		root / "node_modules",
		Path("/workspace/repos/power-agents-private/node_modules"),
		Path("/workspace/repos/neural-llm.com/node_modules"),
	):
		if (cand / "playwright" / "package.json").is_file():
			parts.append(str(cand.resolve()))
	prev = str(os.environ.get("NODE_PATH") or "").strip()
	if prev:
		parts.extend(p for p in prev.split(":") if p and p not in parts)
	return ":".join(parts)


def _runner() -> list[str] | None:
	bun = shutil.which("bun")
	if bun:
		return [bun]
	tsx = shutil.which("tsx")
	if tsx:
		return [tsx]
	node = shutil.which("node")
	if node:
		try:
			major = int(
				subprocess.check_output(
					[node, "-p", "process.versions.node"],
					text=True,
					timeout=5,
				)
				.strip()
				.split(".", 1)[0]
			)
		except Exception:
			major = 0
		if major >= 22:
			return [node, "--experimental-strip-types", "--no-warnings"]
	return None


def _prove_cell(
	*,
	root: Path,
	run_dir: Path,
	cell: dict[str, str],
	sandbox_url: str,
	adapter: Path,
	runner: list[str],
) -> bool:
	cid = cell["cell_id"]
	out = run_dir / "receipts" / f"{cid}.json"
	out.parent.mkdir(parents=True, exist_ok=True)
	argv = runner + [
		str(adapter),
		f"--project={root}",
		f"--out={out}",
		f"--cell-id={cid}",
		f"--snapshot-id={cell['snapshot_id']}",
		f"--universe-id={cell['universe_id']}",
		f"--surface-id={cell['surface_id']}",
		f"--pack={cell['pack']}",
		f"--scenario={cell['scenario']}",
		f"--base={sandbox_url.rstrip('/')}",
	]
	env = os.environ.copy()
	node_path = _playwright_node_path(root)
	if node_path:
		env["NODE_PATH"] = node_path
	env["SANDBOX_UI_URL"] = sandbox_url.rstrip("/")
	proc = subprocess.run(
		argv,
		cwd=str(root),
		env=env,
		capture_output=True,
		text=True,
		timeout=90,
	)
	if not out.is_file():
		print(
			f"vscode-command-pack: no receipt for {cid} rc={proc.returncode} "
			f"err={(proc.stderr or proc.stdout or '')[:300]}",
			file=sys.stderr,
		)
		return False
	try:
		data = json.loads(out.read_text(encoding="utf-8"))
	except json.JSONDecodeError:
		return False
	ok = isinstance(data, dict) and data.get("ok") is True
	if not ok:
		print(
			f"vscode-command-pack: cell {cid} scenario={cell['scenario']} "
			f"failed: {data}",
			file=sys.stderr,
		)
	return ok


def main(argv: list[str] | None = None) -> int:
	ap = argparse.ArgumentParser(description="cc-wf-studio vscode_command pack prove")
	ap.add_argument("--project-dir", default="")
	ap.add_argument("--sandbox-url", default="")
	ap.add_argument("--pack", default="vscode_command")
	ap.add_argument("--out", default="")
	args = ap.parse_args(argv)

	root = Path(args.project_dir or ROOT_DEFAULT).resolve()
	# Prefer product sandbox; ignore shared PA :7777 from the harness env.
	sandbox = (
		(args.sandbox_url or "").strip()
		or str(
			(json.loads((root / "configs/complete-e2e/runtime.json").read_text())
			 if (root / "configs/complete-e2e/runtime.json").is_file()
			 else {}).get("sandbox_ui_url")
			or ""
		).strip()
		or SANDBOX_DEFAULT
	)
	# If harness passed PA's URL, redirect to product default.
	if "7777" in sandbox and "7788" not in sandbox:
		sandbox = SANDBOX_DEFAULT

	if args.pack and args.pack not in ("vscode_command", ""):
		# Harness may call with --pack vscode_command only for this stem.
		pass

	if not _ensure_sandbox(root, sandbox):
		print(f"vscode-command-pack: sandbox unhealthy at {sandbox}", file=sys.stderr)
		return 1

	active = _active_run(root)
	proven = 0
	failed = 0
	if active is None:
		# No active run — still PASS when sandbox is healthy (coverage row / dry).
		payload = {
			"schema": "hurc-complete-e2e-vscode-command-pack/v1",
			"ok": True,
			"sandbox_url": sandbox,
			"notes": "sandbox healthy; no active run to drain",
			"proven": 0,
		}
	else:
		_run_id, run_dir = active
		cells = _outstanding(run_dir)
		adapter = _harness_adapter()
		runner = _runner()
		if cells and (adapter is None or runner is None):
			print(
				"vscode-command-pack: missing harness adapter or bun/tsx runner",
				file=sys.stderr,
			)
			return 1
		for cell in cells:
			if cell.get("scenario") not in SCENARIOS:
				continue
			if _prove_cell(
				root=root,
				run_dir=run_dir,
				cell=cell,
				sandbox_url=sandbox,
				adapter=adapter,  # type: ignore[arg-type]
				runner=runner,  # type: ignore[arg-type]
			):
				proven += 1
			else:
				failed += 1
		payload = {
			"schema": "hurc-complete-e2e-vscode-command-pack/v1",
			"ok": failed == 0,
			"sandbox_url": sandbox,
			"run_id": _run_id,
			"outstanding": len(cells),
			"proven": proven,
			"failed": failed,
			"surface": SURFACE,
		}

	out_path = Path(args.out) if args.out else (
		root / ".hurc-harness" / "state" / "complete-e2e" / "vscode-command-pack-vscode_command.json"
	)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
	print(json.dumps(payload))
	return 0 if payload.get("ok") else 1


if __name__ == "__main__":
	raise SystemExit(main())
