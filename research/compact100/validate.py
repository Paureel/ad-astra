# SPDX-License-Identifier: Apache-2.0
"""Replay the frozen research sources in a disposable directory.

Default: independent numerical/symbolic checks. --full also reruns the exact
main-shell enclosure and the inherited core and reference interval calculations.
No original benchmark, source receipt, promotion gate, or viewer state is edited.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from fractions import Fraction as F
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy
import scipy

ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from research.compact100.geometry import UPSTREAM, CANDIDATE, EXPECTED_HASH, CompactGeometry
from research.compact100.bounds import compact_floor, outward, necessary_radius

HERE = Path(__file__).resolve().parent
MAIN = "research/radical_compact/tensor_validation/bernstein_replay.py"
MAIN_FROZEN = "research/radical_compact/tensor_validation/tensor-polished-final-verified.json"
MAIN_REPLAY = "research/radical_compact/tensor_validation/local-replay.json"
CORE = "research/expanded_family/radial_control/log_cylinder_caps.py"
CORE_RECEIPT = "research/expanded_family/radial_control/log-cylinder-caps-core-level-9.json"
REFERENCE = "research/deep_strict/validated_math/enclose_frozen.py"
REFERENCE_RECEIPT = "research/deep_strict/validated_math/frozen-interval-level-11.json"
CANDIDATE_PATH = str(CANDIDATE.relative_to(UPSTREAM))


def digest(path): return sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())


def check_sources():
    manifest = read(HERE/"upstream-manifest.json")
    for name, expected in manifest["files"].items():
        if digest(UPSTREAM/name) != expected:
            raise ValueError("Frozen research source differs: "+name)
    if digest(CANDIDATE) != EXPECTED_HASH:
        raise ValueError("The selected candidate differs from the supplied PDF/archive.")
    CompactGeometry()
    return manifest


def run(full=False, output=ROOT/"results/local/compact100"):
    manifest = check_sources()
    output = Path(output).resolve()
    if output == UPSTREAM.resolve() or UPSTREAM.resolve() in output.parents:
        raise ValueError("Replay output must not modify frozen sources.")
    output.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="replay-", dir=output))
    shutil.copytree(UPSTREAM, work, dirs_exist_ok=True)
    environment = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONPATH=str(ROOT/"src"))
    jobs = {
        "cartesian": ["research/radical_compact/tensor_cartesian_audit.py", CANDIDATE_PATH, "--receipt", MAIN_FROZEN],
        "symbolic": ["research/radical_compact/variational_physics/tensor_identity_audit.py"],
        "clipped-log": ["research/radical_compact/variational_physics/clipped_log_bound.py"],
        "radius": ["research/radical_compact/variational_physics/radius_scaling.py"],
        "tail-bound": ["research/radical_compact/variational_physics/conditional_tail_bound.py"],
    }
    if full:
        jobs.update({"main": [MAIN, CANDIDATE_PATH, "--tolerance", "1/20", "--name", "local-replay"],
                     "core": [CORE, "9"], "reference": [REFERENCE, "11", "10"]})
    commands = []
    def execute(item):
        name, args = item
        command = [sys.executable, *args]
        with (output/(name+".log")).open("w") as log:
            subprocess.run(command, cwd=work, env=environment, stdout=log, stderr=subprocess.STDOUT, check=True)
        return {"name": name, "python_arguments": args, "exit_code": 0, "log_sha256": digest(output/(name+".log"))}
    # Original receipt inputs stay frozen while dependent audit jobs finish.
    for name in ("cartesian", "symbolic", "clipped-log", "radius", "tail-bound"):
        commands.append(execute((name, jobs[name])))
    if full:
        with ThreadPoolExecutor(max_workers=3) as pool:
            commands.extend(pool.map(execute, [(n, jobs[n]) for n in ("main", "core", "reference")]))
    original = read(UPSTREAM/MAIN_FROZEN)
    core, reference = read(work/CORE_RECEIPT), read(work/REFERENCE_RECEIPT)
    replay = read(work/MAIN_REPLAY) if full else original
    mathematical_fields = ["cells", "total_energy_upper_J_exact", "main_energy_J_interval_outward",
        "base_cells_completed", "cap_subdivision_cells", "energy_subdivision_cells", "all_global_caps_pass",
        "complete_domain_covered", "C5_core_exterior_and_angular_matching_pass"]
    if full:
        for key in mathematical_fields:
            if replay[key] != original[key]:
                raise ValueError("The full replay changed a mathematical result: "+key)
        old_core, old_ref = read(UPSTREAM/CORE_RECEIPT), read(UPSTREAM/REFERENCE_RECEIPT)
        for key in ["rational_proof", "core_integral", "core_energy_upper_J_exact_rational"]:
            if core[key] != old_core[key]: raise ValueError("Core replay differs: "+key)
        if reference["baseline_energy_J_interval"] != old_ref["baseline_energy_J_interval"]:
            raise ValueError("Reference enclosure replay differs.")
    upper = F(replay["total_energy_upper_J_exact"])
    reference_lower, reference_upper = map(F, reference["baseline_energy_J_interval"])
    floor_lower, floor_upper = compact_floor(F(100))
    saving = 100*(1-upper/reference_lower)
    numerical = read(work/"research/radical_compact/tensor-polished-candidate-cartesian-audit.json")
    result = {
        "schema_version": 1, "status": "numerical_only", "formal_certification": False,
        "evidence_kind": "replayed_exact_continuum_enclosure_and_independent_numerical_audit" if full else "independent_numerical_and_symbolic_audit_with_frozen_enclosures",
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": sys.version, "numpy": numpy.__version__, "scipy": scipy.__version__},
        "source_archive_sha256": manifest["source_archive_sha256"], "candidate_sha256": EXPECTED_HASH,
        "upstream_manifest_sha256": digest(HERE/"upstream-manifest.json"),
        "model_source_sha256": digest(HERE/"geometry.py"), "runner_source_sha256": digest(__file__),
        "scenario": "compact100-research", "original_v1_benchmark_eligible": False,
        "full_main_core_and_reference_replayed": full,
        "all_main_global_caps_pass": replay["all_global_caps_pass"],
        "exact_cabin_and_C5_matching": replay["C5_core_exterior_and_angular_matching_pass"],
        "energy_J_interval": [replay["main_energy_J_interval_outward"][0], replay["total_energy_upper_J_outward"]],
        "energy_upper_exact": str(upper), "reference_energy_J_interval": [str(reference_lower), str(reference_upper)],
        "guaranteed_saving_percent": outward((saving, saving)),
        "conditional_compact_class_floor_J": outward((floor_lower, floor_upper)),
        "upper_over_class_infimum_ceiling": outward((upper/floor_upper, upper/floor_lower)),
        "conditional_necessary_radius_m": {str(f): outward(necessary_radius(F(f), reference_upper=reference_upper)) for f in (10, 100)},
        "base_cells": replay["base_cells_completed"], "cap_checks": replay["cap_subdivision_cells"],
        "energy_cells": replay["energy_subdivision_cells"], "core_energy_upper_J": core["core_energy_upper_J_exact_rational"],
        "independent_energy_refinement": numerical["energy_refinement"],
        "replay_commands": commands,
        "mathematical_digest": sha256(json.dumps({k: replay[k] for k in mathematical_fields}, sort_keys=True).encode()).hexdigest(),
        "limitations": ["Ordinary computer-assisted interval/rational verification; no formal Lean GR certificate.",
            "A broader shape family and redesigned exterior, not an entry in the unchanged v1 benchmark.",
            "Peak stress and curvature are separate sampled diagnostics, not certified extrema.",
            "No material source, startup, stability, causal control, or physical propulsion demonstration."],
    }
    (output/"result.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"replay_commands", "independent_energy_refinement"}}, indent=2), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT/"results/local/compact100")
    args = parser.parse_args()
    run(args.full, args.output)
