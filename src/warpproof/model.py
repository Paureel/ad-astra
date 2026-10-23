"""Exact input schema and the trusted, restricted geometry decoder."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PATH = ROOT / "benchmarks" / "rodal-2c-v1.json"
RATIONAL = re.compile(r"^-?[0-9]+(?:/[1-9][0-9]*)?$")


def canonical_hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def exact(value: str) -> Fraction:
    if not isinstance(value, str) or len(value) > 128 or not RATIONAL.fullmatch(value):
        raise ValueError("Parameters must be short exact rational strings, for example '1/1000'.")
    return Fraction(value)


def benchmark() -> dict:
    return json.loads(BENCHMARK_PATH.read_text())


@dataclass(frozen=True)
class Candidate:
    id: str
    terms: tuple[tuple[int, int, Fraction], ...]
    source: dict
    raw_input_sha256: str | None = None

    @property
    def parameter_hash(self) -> str:
        return canonical_hash({"benchmark_sha256": canonical_hash(benchmark()), "terms": [
            [i, j, str(a)] for i, j, a in self.terms]})

    @property
    def candidate_hash(self) -> str:
        return canonical_hash(self.source)


def decode_candidate(data: dict) -> Candidate:
    if not isinstance(data, dict):
        raise ValueError("Candidate must be a JSON object.")
    allowed = {"schema_version", "id", "benchmark", "coefficients", "description"}
    if set(data) - allowed:
        raise ValueError(f"Unknown candidate fields: {sorted(set(data)-allowed)}")
    spec = benchmark()
    if type(data.get("schema_version")) is not int or data.get("schema_version") != 1 or data.get("benchmark") != spec["id"]:
        raise ValueError("Unrecognized candidate schema or benchmark.")
    if "description" in data and (not isinstance(data["description"], str) or len(data["description"]) > 4000):
        raise ValueError("Description must be text of at most 4000 characters.")
    name = data.get("id")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", name):
        raise ValueError("Candidate id must be a short lowercase ASCII identifier.")
    rows = data.get("coefficients")
    if not isinstance(rows, list) or len(rows) > 9:
        raise ValueError("At most nine coefficient records are allowed.")
    seen, terms = set(), []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"x_power", "transverse_power", "coefficient"}:
            raise ValueError("Each term must specify x_power, transverse_power and coefficient.")
        i, j = row["x_power"], row["transverse_power"]
        if type(i) is not int or type(j) is not int or min(i, j) < 0 or i + 2*j > 4:
            raise ValueError("Terms must have nonnegative integer powers and x_power+2*transverse_power<=4.")
        if (i, j) in seen:
            raise ValueError("Duplicate polynomial term.")
        seen.add((i, j))
        a = exact(row["coefficient"])
        if abs(a) > exact(spec["family"]["maximum_abs_coefficient"]):
            raise ValueError("Coefficient exceeds the frozen absolute bound.")
        if a:
            terms.append((i, j, a))
    return Candidate(name, tuple(sorted(terms)), data)


def load_candidate(path: str | Path) -> Candidate:
    path = Path(path)
    if path.stat().st_size > 65536:
        raise ValueError("Candidate file exceeds the 64 KiB limit.")
    def no_duplicates(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError(f"Duplicate JSON key: {k}")
            out[k] = v
        return out
    raw = path.read_bytes()
    item = decode_candidate(json.loads(raw, object_pairs_hook=no_duplicates))
    return Candidate(item.id, item.terms, item.source, sha256(raw).hexdigest())


def baseline_candidate() -> Candidate:
    return load_candidate(ROOT / "candidates" / "rodal-baseline.json")


def make_candidate(terms: dict[tuple[int, int], Fraction], name: str = "search-candidate") -> Candidate:
    return decode_candidate({"schema_version": 1, "id": name,
        "benchmark": benchmark()["id"],
        "coefficients": [{"x_power": i, "transverse_power": j, "coefficient": str(v)}
                         for (i, j), v in sorted(terms.items()) if v]})

