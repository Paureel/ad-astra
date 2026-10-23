"""Check that source packaging leaves machine state and credential fixtures out."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_release", SOURCE / "scripts/package_release.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class PackagingTests(unittest.TestCase):
    def populate(self, root):
        (root / ".gitignore").write_text((SOURCE / ".gitignore").read_text())
        fixtures = ["source.py", ".env", ".env.example", ".netrc", "private.key",
                    ".tools/cache.bin", ".venv/runtime", "results/local/run.json",
                    "research/local/notes.txt", "trace.log", "archive.zip"]
        for name in fixtures:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Non-sensitive packaging test fixture.\n")

    def test_git_checkout_respects_ignored_and_local_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.populate(root)
            subprocess.run(["git", "init", "--quiet", str(root)], check=True)
            with patch.object(release, "ROOT", root):
                files = {path.relative_to(root).as_posix() for path in release.included_files()}
            self.assertEqual(files, {".gitignore", ".env.example", "source.py"})

    def test_extracted_source_also_excludes_credentials_and_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.populate(root)
            with patch.object(release, "ROOT", root):
                files = {path.relative_to(root).as_posix() for path in release.included_files()}
            self.assertEqual(files, {".gitignore", ".env.example", "source.py"})


if __name__ == "__main__":
    unittest.main()
