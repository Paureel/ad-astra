"""Package the source checkout and verify its manifest using the standard library.

Run from any directory. Runtime environments and generated compiler caches are
excluded. Included scientific result files are preserved as generated evidence.
"""
from __future__ import annotations

import argparse
import fnmatch
from hashlib import sha256
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "venv", ".tools", "node_modules", ".lake", "__pycache__", "build", "dist", ".DS_Store", ".aws", ".ssh", ".openai", ".codex", ".idea", ".cache", ".npm", ".pnpm-store", ".pytest_cache", ".mypy_cache", ".ruff_cache", "htmlcov"}


def included_files():
    files = []
    # Honor .gitignore in a checkout, including reviewable new source files.
    # A source archive also works without Git installed.
    if (ROOT / ".git").exists():
        listing = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT)
        paths = [ROOT / name.decode("utf-8") for name in listing.split(b"\0") if name]
    else:
        paths = ROOT.rglob("*")
    for path in sorted(set(paths)):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED or part.endswith(".egg-info") or part.startswith("pip-")
               for part in relative.parts):
            continue
        if relative.as_posix().startswith(("results/local/", "research/local/")):
            continue
        if path.name.startswith(".env") and path.name not in (".env.example", ".env.sample"):
            continue
        if path.name in (".git-credentials", ".netrc", ".npmrc", ".pypirc") or relative.as_posix() == ".claude/settings.local.json":
            continue
        if any(fnmatch.fnmatch(path.name, pattern) for pattern in ("*.pem", "*.key", "*.p12", "*.pfx", "*.log", "*.zst", "*.tgz", "*.tar", "*.tar.gz", ".credentials*")):
            continue
        if path.is_symlink():
            raise ValueError(f"Release cannot include a symbolic link: {relative}")
        if path.is_file() and path.name != "MANIFEST.sha256" and path.suffix not in (".pyc", ".zip"):
            files.append(path)
    return files


def manifest_text(files):
    return "".join(f"{sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}\n" for path in files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"build"/"ad-astra-source.zip")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify-manifest", action="store_true")
    mode.add_argument("--manifest-only", action="store_true", help="Refresh hashes without creating an archive.")
    args = parser.parse_args()
    files = included_files()
    manifest = ROOT/"MANIFEST.sha256"
    expected = manifest_text(files)
    if args.verify_manifest:
        if manifest.read_text() != expected:
            raise SystemExit("Manifest differs from this checkout. Regenerate after intentional changes.")
        print(f"PASS: {len(files)} file hashes match MANIFEST.sha256.")
        return
    manifest.write_text(expected)
    if args.manifest_only:
        print(f"Updated manifest: {len(files)} source files.")
        return
    files.append(manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(f"ad-astra/{path.relative_to(ROOT).as_posix()}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(f"Packaged {len(files)} files: {args.output}")
    print(f"SHA256 {sha256(args.output.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
