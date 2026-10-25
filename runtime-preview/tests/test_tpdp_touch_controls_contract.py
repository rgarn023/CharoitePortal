"""TPDP's native touch controls send held X11 keys through Winlator XServer."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CONTROLS=(ROOT/"CharoiteTpdpTouchControls.java").read_text()
OVERLAY=(ROOT/"overlay.py").read_text()
CORE=(ROOT/"charoite-core/CharoiteCore.java").read_text()
SESSION=(ROOT/"charoite-core/CharoiteGameSessions.java").read_text()

class TpdpTouchContract(unittest.TestCase):
    def test_real_native_keyboard_keys(self):
        keys=(
            "KEY_UP","KEY_DOWN","KEY_LEFT","KEY_RIGHT","KEY_Z",
            "KEY_X","KEY_C","KEY_S","KEY_A","KEY_D","KEY_SPACE",
            "KEY_SHIFT_L","KEY_ENTER","KEY_ESC",
        )
        for key in keys:
            self.assertIn("XKeycode."+key,CONTROLS)
        for event in ("MotionEvent.ACTION_DOWN","MotionEvent.ACTION_UP",
                      "MotionEvent.ACTION_CANCEL","releaseAll()",
                      "xServer.injectKeyPress(key)","xServer.injectKeyRelease(key)"):
            self.assertIn(event,CONTROLS)
        self.assertNotIn("setKeysyms(",CONTROLS)

    def test_safely_scope_overlay_to_tpdp_on_phone(self):
        for token in ('CharoiteTpdpTouchControls.attach(this,rootView,xServer)',
                      'tpdp_controls_target.write_bytes(tpdp_controls_source.read_bytes())',
                      'getIntent().hasExtra("exec_path")',
                      'isTpdpGameExecutable(',
                      'getBooleanExtra("touhou_desktop_window", false)'):
            self.assertIn(token,OVERLAY)
        self.assertIn('file.equals("gn_enbu.exe")',CORE)
        self.assertIn('file.equals("enbu_ap.exe")',CORE)
        self.assertIn("TPDP_GRAPHICS_WINED3D_VIRGL",CORE)
        self.assertIn('play.putExtra("charoite_tpdp_graphics_mode"',SESSION)

    def test_runtime_not_mutated_by_overlay(self):
        for token in ("container.saveData(","setKeysyms(","deleteRecursively",
                      "FileOutputStream"):
            self.assertNotIn(token,CONTROLS)
        self.assertIn('HIDE KEYS',CONTROLS)
        self.assertIn('SHOW KEYS',CONTROLS)

if __name__=="__main__":
    unittest.main()
