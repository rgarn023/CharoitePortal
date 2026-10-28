"""Fail-closed and source-provenance checks for Charoite Wine (no runner downloads)."""
import pathlib
import unittest

WINE = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = (WINE / "prepare-source.sh").read_text(encoding="utf-8")


class SourceContract(unittest.TestCase):
    def test_exact_pinned_base(self):
        self.assertIn("c74acb09d51b447f5d5ac56c87608d3ec565a767", SCRIPT)
        self.assertIn('git checkout --detach "$base_sha"', SCRIPT)
        self.assertIn('[[ "$(git rev-parse HEAD)" == "$base_sha" ]]', SCRIPT)

    def test_never_overwrite_existing_workspaces(self):
        self.assertIn('if [[ -e "$workspace" ]]; then', SCRIPT)
        self.assertIn('Refusing existing destination', SCRIPT)
        self.assertNotIn("rm -rf", SCRIPT)
        self.assertNotIn("sudo ", SCRIPT)

    def test_no_manual_prerequisite_bypass(self):
        self.assertNotIn("CHAROITE_WINE_PREREQUISITES_PREPARED", SCRIPT)
        self.assertIn("CHAROITE_WINE_PREREQUISITES_APPLIED=", SCRIPT)
        self.assertIn("git apply --check", SCRIPT)
        self.assertIn("git diff --check", SCRIPT)

    def test_vendor_patch_provenance(self):
        patched = sorted((WINE / "patches").glob("*.patch"))
        self.assertEqual(len(patched), 2)
        text = (WINE / "README.md").read_text()
        for patch in patched:
            self.assertIn(patch.name.split("-", 1)[0], text)
            self.assertIn("diff --git", patch.read_text())
        self.assertTrue((WINE / "UPSTREAM-WEHAVEPHONES-LICENSE.txt").is_file())

    def test_no_anti_cheat_evasion(self):
        self.assertNotIn("antiCheatDisable", SCRIPT)
        self.assertNotIn("kernelBypass", SCRIPT)

if __name__ == "__main__":
    unittest.main()
