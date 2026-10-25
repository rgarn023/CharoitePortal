"""TPDP touch-keyboard overlay must be scoped and hold keys safely."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CONTROLS=(ROOT/"charoite-core/CharoiteTpdpTouchControls.java").read_text()
OVERLAY=(ROOT/"overlay.py").read_text()
CORE=(ROOT/"charoite-core/CharoiteCore.java").read_text()
SESSION=(ROOT/"charoite-core/CharoiteGameSessions.java").read_text()

class TpdpTouchContract(unittest.TestCase):
    def test_touch_buttons_send_real_tpdp_keyboard_keys(self):
        expected={
            "KEYCODE_DPAD_UP","KEYCODE_DPAD_DOWN",
            "KEYCODE_DPAD_LEFT","KEYCODE_DPAD_RIGHT",
            "KEYCODE_Z","KEYCODE_X","KEYCODE_C","KEYCODE_S",
            "KEYCODE_A","KEYCODE_D","KEYCODE_SPACE",
        }
        for key in expected:
            self.assertIn("KeyEvent."+key,CONTROLS)
        self.assertIn("KeySink", CONTROLS)
        self.assertIn("MotionEvent.ACTION_DOWN",CONTROLS)
        self.assertIn("MotionEvent.ACTION_UP",CONTROLS)
        self.assertIn("MotionEvent.ACTION_CANCEL",CONTROLS)
        self.assertIn("sink.send(code,false)",CONTROLS)
        # Do not convert the keyboard game into an XInput controller.
        self.assertNotIn("XboxController", CONTROLS)
        self.assertNotIn("setController", CONTROLS)

    def test_only_tpdp_windows_games_have_overlay(self):
        self.assertIn("CharoiteTpdpTouchControls.java", OVERLAY)
        self.assertIn("CharoiteTpdpTouchControls.attach(",OVERLAY)
        self.assertIn("isTpdpGameExecutable(",OVERLAY)
        self.assertIn('getIntent().hasExtra("exec_path")',OVERLAY)
        self.assertIn('getBooleanExtra("touhou_desktop_window", false)',OVERLAY)
        self.assertIn("xServer.keyboard.onKeyEvent",OVERLAY)
        self.assertIn("file.equals(\\"gn_enbu.exe\\")",CORE)
        self.assertIn("file.equals(\\"enbu_ap.exe\\")",CORE)
        # Existing reversible DirectX backend selection remains available.
        self.assertIn("TPDP_GRAPHICS_WINED3D_VIRGL",CORE)
        self.assertIn('play.putExtra("charoite_tpdp_graphics_mode"',SESSION)

    def test_overlay_has_no_persisted_game_or_container_changes(self):
        self.assertNotIn("ContainerManager",CONTROLS)
        self.assertNotIn("delete",CONTROLS)
        self.assertNotIn("SharedPreferences",CONTROLS)
        self.assertNotIn("FileOutputStream",CONTROLS)

if __name__=="__main__":
    unittest.main()
