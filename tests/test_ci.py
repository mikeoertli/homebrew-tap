import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("ci", Path(__file__).parents[1] / "scripts/ci.py")
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class SelectionTests(unittest.TestCase):
    def test_private_and_unpublished_packages_are_excluded(self):
        lock = {"public": {"private": False, "commit": "a" * 40},
                "private": {"private": True, "commit": "b" * 40},
                "pending": {"private": False}}
        files = ["Formula/public.rb", "Formula/private.rb", "Formula/pending.rb",
                 "README.md", "templates/public.rb.in", "Formula/unknown.rb"]
        self.assertEqual(ci.select(lock, files), ["public"])

    def test_newly_bootstrapped_public_packages_are_included(self):
        lock = {"newtool": {"private": False, "commit": "a" * 40}}
        self.assertEqual(ci.select(lock, ["Formula/newtool.rb"]), ["newtool"])


if __name__ == "__main__":
    unittest.main()
