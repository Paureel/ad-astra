"""Attribution checks using an isolated Git fixture, never a scientific record."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_viewer_history.py"
SPEC = importlib.util.spec_from_file_location("viewer_history", SCRIPT)
history = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(history)


class HistoryAuthorTests(unittest.TestCase):
    def test_explicit_user_attribution_is_preserved(self):
        author = {"name": "Paureel", "source": "user-assigned attribution"}
        self.assertEqual(history.resolve_author(author), author)

    def test_invalid_commit_cannot_be_used_as_an_option(self):
        with self.assertRaisesRegex(ValueError, "full Git commit"):
            history.resolve_author({"git_commit": "--all"})

    def test_exact_git_commit_supplies_author_without_guessing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, text=True,
                                               stderr=subprocess.DEVNULL).strip()
            git("init", "--initial-branch=fixture")
            git("-c", "user.name=Interface Fixture Author", "-c", "user.email=fixture@example.invalid",
                "commit", "--allow-empty", "-m", "Isolated attribution test")
            revision = git("rev-parse", "HEAD")
            with patch.object(history, "ROOT", root):
                author = history.resolve_author({"git_commit": revision})
            self.assertEqual(author["name"], "Interface Fixture Author")
            self.assertEqual(author["git_commit"], revision)
            self.assertEqual(author["source"], "Git commit author")


if __name__ == "__main__":
    unittest.main()
