"""Safety and integration contract for the TPDP touch keyboard."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CONTROLS=(ROOT/"CharoiteTpdpTouchControls.java").read_text()
OVERLAY=(ROOT/"overlay.py").read_text()
CORE=(ROOT/"charoite-core/CharoiteCore.java").read_text()
SESSION=(ROOT/"charoite-core/CharoiteGameSessions.java").read_text()

class TpdpTouchContract(unittest.TestCase):
    def test_real_holdable_keyboard_keys(self):
        self.assertIn("package com.charoitegames.core;",CONTROLS)
        for name in ("KEY_UP","KEY_DOWN","KEY_LEFT","KEY_RIGHT",
                     "KEY_Z","KEY_X","KEY_C","KEY_S","KEY_A","KEY_D",
                     "KEY_SPACE","KEY_SHIFT_L","KEY_ENTER","KEY_ESC"):
            self.assertIn("XKeycode."+name,CONTROLS)
        for marker in (
            "MotionEvent.ACTION_DOWN","MotionEvent.ACTION_UP",
            "MotionEvent.ACTION_CANCEL","xServer.injectKeyPress(key)",
            "xServer.injectKeyRelease(key)","releaseAll()",
            "HIDE KEYS","SHOW KEYS"
        ):
            self.assertIn(marker,CONTROLS)
        self.assertNotIn("XboxController",CONTROLS)

    def test_tpdp_only_and_package_matches_overlay(self):
        self.assertIn("CharoiteTpdpTouchControls.java",OVERLAY)
        self.assertIn("com/charoitegames/core/CharoiteTpdpTouchControls.java",OVERLAY)
        self.assertIn("CharoiteTpdpTouchControls.attach(",OVERLAY)
        self.assertIn("this, rootView, xServer);",OVERLAY)
        self.assertIn("isTpdpGameExecutable(",OVERLAY)
        self.assertIn('getIntent().hasExtra("exec_path")',OVERLAY)
        self.assertIn('getBooleanExtra("touhou_desktop_window", false)',OVERLAY)
        self.assertIn('file.equals("gn_enbu.exe")',CORE)
        self.assertIn('file.equals("enbu_ap.exe")',CORE)

    def test_no_container_or_save_mutations(self):
        for forbidden in ("ContainerManager","deleteRecursively",
                          "FileOutputStream","SharedPreferences","setDXWrapper"):
            self.assertNotIn(forbidden,CONTROLS)
        self.assertIn('play.putExtra("charoite_tpdp_graphics_mode"',SESSION)

if __name__=="__main__":
    unittest.main()
