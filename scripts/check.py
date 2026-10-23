"""Run the contributor checks with the current (normally virtualenv) Python."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(command, *, cwd=ROOT, env=None):
    print("+ " + " ".join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=cwd, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formal", action="store_true", help="Also build and audit the pinned Lean library.")
    args = parser.parse_args()
    if not shutil.which("node") or not shutil.which("npm"):
        parser.error("Node 18+ and npm are required; the viewer has no npm dependencies to install.")
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    run([sys.executable, "formal/diagnostics/direct_ricci_check.py"])
    run(["npm", "test"])
    run(["npm", "run", "build"])
    gate = subprocess.run([sys.executable, "-m", "warpproof", "verify", "--require-formal"],
                          cwd=ROOT, capture_output=True, text=True)
    try:
        result = json.loads(gate.stdout)
    except json.JSONDecodeError:
        raise SystemExit("Formal gate did not return its expected structured refusal.\n" + gate.stderr)
    if gate.returncode != 2 or result.get("accepted") is not False or result.get("formal_certification") is not False:
        raise SystemExit("Formal promotion must refuse with exit 2, accepted=false, and formal_certification=false.")
    print("PASS: incomplete formal certification is explicitly refused.", flush=True)
    if args.formal:
        env = dict(os.environ)
        local_lean = ROOT / ".tools/lean-4.35.0-darwin_aarch64/bin"
        if not shutil.which("lake") and (local_lean / "lake").is_file():
            env["PATH"] = str(local_lean) + os.pathsep + env.get("PATH", "")
        if not shutil.which("lake", path=env.get("PATH")):
            raise SystemExit("Install the pinned Lean toolchain; see formal/README.md. Formal checks were not run.")
        run(["lake", "build"], cwd=ROOT / "formal", env=env)
        run(["lake", "env", "lean", "Audit.lean"], cwd=ROOT / "formal", env=env)
    print("PASS: contributor checks complete; no record promotion or deployment.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode)
