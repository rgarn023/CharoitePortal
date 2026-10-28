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
        self.assertIn("patches/SERIES", SCRIPT)
        self.assertIn("git diff --check", SCRIPT)

    def test_vendor_patch_provenance(self):
        patched = sorted((WINE / "patches").glob("*.patch"))
        self.assertEqual(len(patched), 8)
        active = (WINE / "patches/SERIES").read_text()
        active_patches = [line.strip() for line in active.splitlines()
                          if line.strip() and not line.lstrip().startswith("#")]
        self.assertEqual(len(active_patches), 7)
        self.assertEqual(len(active_patches), len(set(active_patches)))
        self.assertEqual(set(active_patches),
                         {p.name for p in patched} -
                         {"0001-arm64ec-copyable-syscalls-and-thread-grace.patch"})
        self.assertIn("0500-arm64ec-no-spurious-libgcc.patch", active_patches)
        self.assertIn("0600-arm64ec-clipboard-winsock-buffers.patch", active_patches)
        self.assertNotIn("0500-arm64ec-clang-compiler-rt.patch", active_patches)
        self.assertIn("0100-arm64ec-syscall-stubs-and-thread-grace.patch",active)
        self.assertIn("0002-android-external-file-ownership.patch",active)
        self.assertIn("0200-android-machine-id-fallback.patch",active)
        self.assertNotIn("\n0001-arm64ec-copyable-syscalls-and-thread-grace.patch",active)
        safety = (WINE / "patches/0200-android-machine-id-fallback.patch").read_text()
        self.assertIn("FILE *f = NULL", safety)
        self.assertIn("if (!f)", safety)
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
