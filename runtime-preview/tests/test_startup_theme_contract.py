"""Regression gates for Charoite Portal's Windows startup presentation.

The preloader must be UI-only and preserve upstream XServer session lifecycle.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = (ROOT / "overlay.py").read_text(encoding="utf-8")
STARTUP = (ROOT / "CharoiteStartupScreen.java").read_text(encoding="utf-8")
HOOK = (ROOT / "charoite-core/japanese/touhou_font_hook.c").read_text(encoding="utf-8")

class StartupThemeContract(unittest.TestCase):
    def test_full_screen_loading_view_is_portal_owned(self):
        self.assertIn("com.winlator.CharoiteStartupScreen.create(activity)", OVERLAY)
        self.assertIn("CharoiteThemes.defaultWallpaper(theme, true)", STARTUP)
        self.assertIn("CHAROITE PORTAL", STARTUP)
        self.assertIn("C H A R O I T E   C O R E", STARTUP)
        self.assertIn("com.winlator.R.id.TextView", STARTUP)

    def test_windows_lifecycle_and_data_are_not_replaced(self):
        self.assertIn("preloaderDialog.closeOnUiThread()", OVERLAY)
        self.assertNotIn("startActivity(", STARTUP)
        self.assertNotIn("deleteRecursively", STARTUP)
        self.assertNotIn("WineUtils", STARTUP)

    def test_task_diagnostics_cover_owner_draw_without_state_mutations(self):
        self.assertIn("hook-v6 owner-draw checklist paint event detected", HOOK)
        self.assertIn("LBS_HASSTRINGS", HOOK)
        self.assertIn("task-%d utf16=", HOOK)
        self.assertNotIn("SendMessageW(hwnd,LB_DELETESTRING", HOOK)
        self.assertNotIn("LB_SETITEMDATA", HOOK)

if __name__ == "__main__":
    unittest.main()
