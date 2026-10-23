"""Small, data-only command line interface. Formal promotion is fail-closed."""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
import sys

from .energy import evaluate_energy
from .geometry import Geometry
from .model import ROOT, baseline_candidate, benchmark, load_candidate, make_candidate
from .reporting import evaluate_report, reproduce_report, viewer_report, write_report


def search(iterations, output):
    if not 1 <= iterations <= 1000:
        raise ValueError("Search iterations must lie between 1 and 1000.")
    # A reproducible coordinate-search demonstration, not a competitive solver.
    basis = [(1, 0), (3, 0), (1, 1), (0, 0), (2, 0), (4, 0), (0, 1), (2, 1), (0, 2)]
    current = baseline_candidate()
    best = evaluate_energy(Geometry(current))
    original = best["value_J"]
    accepted = 0
    for index in range(iterations):
        term = basis[(index//2) % len(basis)]
        step = Fraction(1 if index % 2 == 0 else -1, 10000)
        terms = {(i, j): a for i, j, a in current.terms}
        terms[term] = terms.get(term, Fraction(0))+step
        if abs(terms[term]) > Fraction(1, 10):
            continue
        proposal = make_candidate(terms, "search-example")
        result = evaluate_energy(Geometry(proposal))
        if not result["warnings"] and result["value_J"]+5*result["error_estimate_J"] < best["value_J"]-5*best["error_estimate_J"]:
            current, best = proposal, result
            accepted += 1
    data = dict(current.source)
    data["id"] = "search-example"
    data["description"] = "Deterministic exploratory coordinate search. Numerical estimate only; global admissibility and certified improvement have not been proved."
    write_report(output, data)
    print(json.dumps({"output": str(output), "iterations": iterations, "accepted_search_steps": accepted,
        "baseline_energy_J": original, "candidate_energy_J": best["value_J"],
        "relative_numerical_reduction": 1-best["value_J"]/original,
        "formal_certification": False, "next_step": "Run evaluate on the saved candidate to check convergence and sampled constraints."}, indent=2))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="A numerical and scoped-proof bootstrap for a fixed 2c warp-geometry energy challenge.")
    commands = parser.add_subparsers(dest="command", required=True)
    reproduction = commands.add_parser("reproduce", help="Compare the published fiducial finite-domain energy table.")
    reproduction.add_argument("--output", default="results/paper-reproduction.json")
    for name in ("evaluate", "render-data"):
        command = commands.add_parser(name)
        command.add_argument("candidate")
        command.add_argument("--output", required=True)
    searching = commands.add_parser("search", help="A small deterministic numerical coordinate search.")
    searching.add_argument("--iterations", type=int, default=8)
    searching.add_argument("--output", default="candidates/search-example.json")
    verification = commands.add_parser("verify", help="Inspect the draft gate; formal verification is intentionally unavailable.")
    verification.add_argument("--require-formal", action="store_true")
    verification.add_argument("--candidate", default=str(ROOT / "candidates" / "rodal-baseline.json"))
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            candidate = load_candidate(args.candidate)
            if args.require_formal:
                print(json.dumps({"accepted": False, "formal_certification": False,
                    "candidate": candidate.id, "status": "blocked",
                    "reason": "The GR bridge, exact input binding, continuum admissibility, and whole-space energy certificate are not implemented. Lean arithmetic fixtures do not discharge these obligations.",
                    "required_next_work": "docs/FORMALIZATION.md and tasks/backlog.json"}, indent=2))
                return 2
            registry = json.loads((ROOT / "records" / "registry.json").read_text())
            if registry.get("certified_records") or benchmark()["formal_status"]["promotion_enabled"]:
                raise ValueError("This bootstrap cannot accept a promoted registry or enabled formal flag.")
            print(json.dumps({"candidate": candidate.id, "schema_valid": True,
                "parameter_hash": candidate.parameter_hash, "formal_certification": False,
                "continuum_admissibility_proved": False, "promotion_enabled": False}, indent=2))
            return 0
        if args.command == "search":
            return search(args.iterations, args.output)
        if args.command == "reproduce":
            result = reproduce_report()
            write_report(args.output, result)
            print(json.dumps({"output": args.output, "comparison_passed": result["comparison_passed"],
                "whole_space_absolute_energy_J": result["whole_space_absolute_energy_J"],
                "standardized_2c_absolute_energy_J": result["standardized_2c_absolute_energy_J"]}, indent=2))
            return 0 if result["comparison_passed"] else 1
        candidate = load_candidate(args.candidate)
        result = viewer_report(candidate) if args.command == "render-data" else evaluate_report(candidate)
        write_report(args.output, result, javascript=args.command == "render-data" and args.output.endswith(".js"))
        print(json.dumps({"output": args.output, "candidate": candidate.id,
            "energy_J": result["energy"]["value_J"], "numerical_status": result["status"]["numerical"],
            "formal_certification": False}, indent=2))
        return 0 if result["status"]["numerical"] == "passed" else 1
    except (ValueError, OSError, ArithmeticError, KeyError) as error:
        print(f"warpproof: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
