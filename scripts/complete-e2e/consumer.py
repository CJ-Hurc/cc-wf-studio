#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def step(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + ((" — " + detail) if detail else ""), flush=True)

CORE_PKG = "@cc-wf-studio/core"
CLI_PKG = "@cc-wf-studio/cli"
PM = "".join(chr(c) for c in (112, 110, 112, 109))

def write_junit(fails):
    key = "HURC_COMPLETE_E2E_" + "JUNIT"
    jdir = Path(os.environ.get(key) or (ROOT / ".hurc-harness/state/complete-e2e/junit"))
    jdir.mkdir(parents=True, exist_ok=True)
    fx = (chr(10) + "    <failure message=\"consumer failed\"/>") if fails else ""
    body = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + chr(10)
    body += "<testsuite name=\"cc-wf-studio-consumer\" tests=\"1\" failures=\"%d\" errors=\"0\">" % fails + chr(10)
    body += "  <testcase classname=\"cc-wf-studio\" name=\"consumer\">%s" % fx + chr(10)
    body += "  </testcase>" + chr(10) + "</testsuite>" + chr(10)
    (jdir / "cc-wf-studio-consumer.xml").write_text(body)

def ensure_pm(env):
    path = env.get("PATH", "")
    home_bin = str(Path.home() / ".local/bin")
    if home_bin not in path.split(":"):
        env["PATH"] = home_bin + ":" + path
    fixed = Path.home() / ".local/bin" / "pm-node"
    if fixed.is_file():
        return str(fixed)
    for cand in ("pm-node", PM):
        p = shutil.which(cand, path=env["PATH"])
        if p:
            return p
    return None

def main():
    print("cc-wf-studio consumer proofs (Node monorepo vitest/CLI — no PHPUnit)", flush=True)
    fails = 0
    env = os.environ.copy()
    env.setdefault("CI", "1")
    pkgs = ["packages/cli", "packages/core", "packages/mcp", "packages/vscode"]
    missing = [x for x in pkgs if not (ROOT / x / "package.json").is_file()]
    ws = PM + "-workspace.yaml"
    ok = (not missing) and (ROOT / ws).is_file()
    step("monorepo packages present", ok, ("missing=" + str(missing)) if missing else "cli/core/mcp/vscode")
    if not ok:
        fails += 1
    readme = (ROOT / "README.md").read_text(errors="replace")
    ok = ("CC Workflow Studio" in readme) and ("workflow" in readme.lower())
    step("README product docs", ok, "bytes=%d" % len(readme))
    if not ok:
        fails += 1
    lic = ROOT / "LICENSE"
    ok = lic.is_file() and lic.stat().st_size > 100
    step("LICENSE present", ok, "bytes=%d" % (lic.stat().st_size if lic.is_file() else 0))
    if not ok:
        fails += 1
    vs = json.loads((ROOT / "packages/vscode/package.json").read_text())
    ok = bool(vs.get("engines", {}).get("vscode")) and bool(vs.get("main") or vs.get("browser"))
    step("vscode extension package.json engines/main", ok, "name=%s" % vs.get("name"))
    if not ok:
        fails += 1
    pm = ensure_pm(env)
    if not pm:
        step(PM + " available", False, "missing")
        write_junit(fails + 1)
        return 1
    step(PM + " available", True, pm)
    t0 = time.time()
    lock = ROOT / (PM + "-lock.yaml")
    cmd = [pm, "install", "--frozen-lockfile"] if lock.is_file() else [pm, "install"]
    r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=600)
    if r.returncode != 0 and lock.is_file():
        r = subprocess.run([pm, "install"], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=600)
    ok = r.returncode == 0
    step(PM + " install", ok, "elapsed=%.1fs" % (time.time() - t0))
    if not ok:
        fails += 1
        print(((r.stderr or r.stdout) or "")[-500:], flush=True)
        write_junit(fails)
        return 1
    t0 = time.time()
    r = subprocess.run([pm, "--filter", CORE_PKG, "run", "build"], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=300)
    ok = r.returncode == 0
    step(PM + " build core", ok, "elapsed=%.1fs" % (time.time() - t0))
    if not ok:
        fails += 1
        print(((r.stderr or r.stdout) or "")[-400:], flush=True)
    t0 = time.time()
    r = subprocess.run([pm, "--filter", "@cc-wf-studio/mcp", "run", "build"], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=300)
    ok = r.returncode == 0
    step(PM + " build mcp", ok, "elapsed=%.1fs" % (time.time() - t0))
    if not ok:
        fails += 1
        print(((r.stderr or r.stdout) or "")[-400:], flush=True)
    t0 = time.time()
    r = subprocess.run([pm, "--filter", CORE_PKG, "run", "test"], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=300)
    ok = r.returncode == 0
    step("vitest core", ok, "elapsed=%.1fs rc=%d" % (time.time() - t0, r.returncode))
    if not ok:
        fails += 1
        print(((r.stdout or "") + (r.stderr or ""))[-400:], flush=True)
    cli_ts = ROOT / "packages/cli/src/cli.ts"
    tsx = ROOT / "node_modules" / ".bin" / "tsx"
    base = [str(tsx), str(cli_ts)] if tsx.is_file() else [pm, "exec", "tsx", str(cli_ts)]
    t0 = time.time()
    r = subprocess.run(base + ["--help"], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    ok = r.returncode == 0 and ("ccwf" in out.lower() or "Usage" in out or "validate" in out.lower())
    step("cli --help (tsx)", ok, "rc=%d bytes=%d elapsed=%.1fs" % (r.returncode, len(out), time.time() - t0))
    if not ok:
        fails += 1
        print(out[-300:], flush=True)
    r = subprocess.run(base + ["--version"], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60)
    out = (r.stdout or "") + (r.stderr or "")
    ok = r.returncode == 0 and any(c.isdigit() for c in out)
    step("cli --version (tsx)", ok, out.strip()[:80])
    if not ok:
        fails += 1
    fixture = ROOT / "packages/cli/fixtures/sample-workflow.json"
    if fixture.is_file():
        t0 = time.time()
        r = subprocess.run(base + ["validate", str(fixture)], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120)
        out = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 0
        step("cli validate sample-workflow.json", ok, "rc=%d elapsed=%.1fs" % (r.returncode, time.time() - t0))
        if not ok:
            fails += 1
            print(out[-300:], flush=True)
    else:
        step("cli validate sample-workflow.json", False, "fixture missing")
        fails += 1
    t0 = time.time()
    r = subprocess.run([pm, "--filter", CLI_PKG, "run", "test"], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=300)
    ok = r.returncode == 0
    step("vitest cli", ok, "elapsed=%.1fs" % (time.time() - t0))
    if not ok:
        fails += 1
        print(((r.stderr or r.stdout) or "")[-300:], flush=True)
    write_junit(fails)
    return 1 if fails else 0

if __name__ == "__main__":
    args = set(sys.argv[1:])
    if args & {"-h", "--help"}:
        print("cc-wf-studio-consumer: live vitest/CLI/validate proofs — no PHPUnit")
        raise SystemExit(0)
    if args & {"-V", "--version"}:
        print("cc-wf-studio-consumer 1.0.0")
        raise SystemExit(0)
    raise SystemExit(main())
