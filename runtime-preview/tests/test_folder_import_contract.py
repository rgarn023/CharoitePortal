"""Core-owned cross-environment import and Japanese-compatibility contracts.

These source-level checks are fast gates. Android CI compiles the Java and
Windows helper binaries; on-device SAF, Wine and gestures still need testing.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text(encoding="utf-8")
CORE_IMPORT = (ROOT / "charoite-core/CharoiteGameImport.java").read_text(encoding="utf-8")
CORE_JAPANESE = (ROOT / "charoite-core/CharoiteJapaneseSupport.java").read_text(encoding="utf-8")
CORE = (ROOT / "charoite-core/CharoiteCore.java").read_text(encoding="utf-8")
OVERLAY = (ROOT / "overlay.py").read_text(encoding="utf-8")


class CoreImportContract(unittest.TestCase):
    def test_policy_is_in_core_and_folder_import_never_autolaunches(self):
        method = CORE_IMPORT.split("public static boolean shouldLaunchAfterImport(", 1)[1]
        method = method.split("public static boolean isLikelyInstaller(", 1)[0]
        self.assertIn("selection == Selection.STANDALONE_INSTALLER", method)
        self.assertNotIn("launchGame(", CORE_IMPORT)
        self.assertNotIn("startActivity(", CORE_IMPORT)
        self.assertIn("CharoiteGameImport.shouldLaunchAfterImport(selection)", PORTAL)
        self.assertIn("INSTALLER_FOLDER", CORE_IMPORT)
        self.assertIn("selection == Selection.GAME_FOLDER || selection == Selection.INSTALLER_FOLDER", CORE_IMPORT)
        self.assertIn("selection == Selection.STANDALONE_INSTALLER", CORE_IMPORT)
        self.assertIn("IMPORT COMPLETE INSTALLER FOLDER", PORTAL)
        self.assertIn("INSTALLER_FOLDER_REQUEST", PORTAL)
        self.assertIn("detectExe(target, selection, touhou)", CORE_IMPORT)
        self.assertIn('new String[]{"setup.exe", "install.exe", "installer.exe"}', CORE_IMPORT)
        self.assertIn("CharoiteGameImport.importSelected(", PORTAL)

    def test_importer_saf_copy_and_protections_are_owned_by_core(self):
        for check in ("DocumentFile.fromTreeUri", "MAX_BYTES", "MAX_FILES", "safeName(",
                      "deleteNewImport(target)", "collectExecutables(",
                      'if (!isLikelyInstaller(candidate)) return candidate;'):
            self.assertIn(check, CORE_IMPORT)
        self.assertNotIn("private void copyFolder(", PORTAL)
        self.assertNotIn("private String detectExe(", PORTAL)

    def test_manual_installer_and_library_launch_remain_explicit(self):
        self.assertIn('outlinedButton("RUN INSTALLER", () -> launchGame(path, true))', PORTAL)
        self.assertIn('installerButton = button("SELECT INSTALLER .EXE"', PORTAL)
        self.assertIn('tile.setOnClickListener(v -> launchGame(path, false))', PORTAL)


class CoreJapaneseCompatibility(unittest.TestCase):
    def test_japanese_fonts_locale_and_helpers_come_from_core(self):
        self.assertIn("package com.charoitegames.core;", CORE_JAPANESE)
        self.assertIn("class CharoiteJapaneseSupport", CORE_JAPANESE)
        self.assertIn("SHIFTJIS", (ROOT / "charoite-core/japanese/touhou_font_hook.c").read_text())
        for path in ("touhou_probe.c", "touhou_font_helper.c",
                     "touhou_font_hook.c", "build_japanese_support.py"):
            self.assertTrue((ROOT / "charoite-core/japanese" / path).is_file())
        self.assertIn("charoite-core/japanese/touhou_probe.exe", OVERLAY)
        self.assertIn("CharoiteJapaneseSupport.ensure(this, rootFS, container)", OVERLAY)

    def test_locale_policy_is_per_realm_and_touhou_default(self):
        self.assertIn("public static boolean japaneseCompatibilityEnabled(Context host)", CORE)
        self.assertIn("CharoiteEnvironments.TOUHOU.equals(environmentId)", CORE)
        self.assertIn("CharoiteCore.japaneseCompatibilityEnabled(", OVERLAY)
        self.assertIn('japaneseButton = outlinedButton("JAPANESE TEXT SUPPORT: OFF"', PORTAL)
        self.assertNotIn('japanese_file = java_root / "com/winlator/TouhouJapaneseSupport.java"', OVERLAY)


if __name__ == "__main__":
    unittest.main()
