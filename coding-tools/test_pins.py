"""pins.py fails on every way an interpreter can differ from the pins."""
from __future__ import annotations

import sys
import unittest
from importlib import metadata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True
import pins                                        # noqa: E402


def installed(versions: dict[str, str]):
    def version(name: str) -> str:
        if name not in versions:
            raise metadata.PackageNotFoundError(name)
        return versions[name]
    return version


class Pins(unittest.TestCase):
    def test_the_pinned_versions_pass(self):
        self.assertEqual(pins.mismatches("# note\na==1.0\n\nb == 2.0  # why\n",
                                         installed({"a": "1.0", "b": "2.0"})), [])

    def test_another_version_is_named_with_both(self):
        self.assertEqual(pins.mismatches("a==1.0\n", installed({"a": "1.1"})),
                         ["a 1.1, pinned 1.0"])

    def test_a_missing_package_fails(self):
        self.assertEqual(pins.mismatches("a==1.0\n", installed({})), ["a missing, pinned 1.0"])

    def test_an_unpinned_line_fails_rather_than_passing_unchecked(self):
        self.assertEqual(pins.mismatches("a>=1.0\n", installed({"a": "1.0"})),
                         ["a>=1.0 is not pinned with ==, so no version can be checked"])

    def test_the_repository_file_parses(self):
        text = pins.REQUIREMENTS.read_text(encoding="utf-8")
        every = {line.split("==")[0]: line.split("==")[1] for line in text.splitlines()
                 if line and not line.startswith("#")}
        self.assertEqual(pins.mismatches(text, installed(every)), [])


if __name__ == "__main__":
    unittest.main()
