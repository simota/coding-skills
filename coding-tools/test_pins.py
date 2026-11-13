"""pins.py fails on every way an interpreter can differ from the pins."""
from __future__ import annotations

import sys
import tempfile
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

    def test_every_form_but_a_plain_pin_is_refused_by_name(self):
        for line in ("a>=1.0", "a[x]==1.0", 'a==1.0; python_version<"3.12"',
                     "-r other.txt", "a==1.0 --hash=sha256:00"):
            with self.subTest(line=line):
                self.assertEqual(pins.mismatches(line + "\n", installed({"a": "1.0"})),
                                 [f"{line} is not a plain name==version pin, "
                                  "so no version can be checked"])

    def test_a_file_saved_with_a_bom_reads_as_pins(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "requirements.txt"
            path.write_bytes("\ufeffa==1.0\n".encode("utf-8"))
            self.assertEqual(pins.mismatches(pins.requirements(path), installed({"a": "1.0"})), [])

    def test_every_line_of_the_repository_file_is_read_as_a_pin(self):
        # Against an interpreter with nothing installed, a line read as a pin is
        # reported missing; a line the parser refuses would be reported refused.
        found = pins.mismatches(pins.requirements(), installed({}))
        self.assertTrue(found)
        for line in found:
            self.assertRegex(line, r"^\S+ missing, pinned \S+$")


if __name__ == "__main__":
    unittest.main()
