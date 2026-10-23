"""Regression checks for the two independent entrypoints to Windows software.

No Android device needed. These tests verify the import-only folder contract at
the Java callsite. The actual Wine/SAF execution still needs phone testing.
"""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "TouhouEntryActivity.java").read_text(encoding="utf-8")


class FolderImportContract(unittest.TestCase):
    def test_folder_picker_is_import_only(self):
        method = SOURCE.split("    private void importGame(Uri uri, boolean folder) {", 1)[1]
        method = method.split("    private static final class Counter", 1)[0]
        self.assertIn("final boolean standaloneExeSelection = !folder;", method)
        self.assertIn("if (standaloneExeSelection) launchGame(selectedPath, true);", method)
        self.assertEqual(method.count("launchGame("), 1)
        self.assertIn("Installer folder imported. Open Setup", method)

    def test_playable_exe_preferred_to_setup_exe(self):
        method = SOURCE.split("    private String detectExe(File root, boolean installer) {", 1)[1]
        method = method.split("    private boolean isLikelyInstaller(", 1)[0]
        self.assertIn("if (!isLikelyInstaller(value)) return value;", method)
        self.assertNotIn("if (isLikelyInstaller(value)) return value;", method)

    def test_manual_setup_launch_available(self):
        self.assertIn('outlinedButton("RUN INSTALLER", () -> launchGame(path, true))', SOURCE)
        self.assertIn('installerButton = button("SELECT INSTALLER .EXE"', SOURCE)

    def test_library_tile_launch_remains_explicit(self):
        self.assertIn('tile.setOnClickListener(v -> launchGame(path, false))', SOURCE)


if __name__ == "__main__":
    unittest.main()
