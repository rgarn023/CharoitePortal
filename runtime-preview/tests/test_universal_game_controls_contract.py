"""Regression checks for installed-game control discovery and real X11 key holds."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILE = (ROOT / "charoite-core/CharoiteGameControlProfiles.java").read_text()
CONTROLS = (ROOT / "charoite-core/CharoiteTpdpTouchControls.java").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()
SESSION = (ROOT / "charoite-core/CharoiteGameSessions.java").read_text()
DISCOVERY = (ROOT / "charoite-core/CharoiteGameDiscovery.java").read_text()
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text()

class UniversalGameControls(unittest.TestCase):
    def test_touhou_eight_documented_pc_keys(self):
        self.assertIn('name.matches("th(0[6789]|1[0-9]|20)', PROFILE)
        self.assertIn('return "touhou_shmup";', PROFILE)
        start = PROFILE.index("private static final int[] TOUHOU_SHMUP")
        end = PROFILE.index("private static final int[] FALLBACK", start)
        keys = PROFILE[start:end]
        for key in ("KEYCODE_DPAD_UP", "KEYCODE_DPAD_LEFT",
                    "KEYCODE_DPAD_RIGHT", "KEYCODE_DPAD_DOWN",
                    "KEYCODE_Z", "KEYCODE_X", "KEYCODE_SHIFT_LEFT",
                    "KEYCODE_CTRL_LEFT", "KEYCODE_ESCAPE"):
            self.assertIn(key, keys)
        self.assertNotIn("KEYCODE_V", keys)

    def test_actual_x11_keys_not_synthetic_android_events(self):
        self.assertIn('xServer.injectKeyPress(key);', OVERLAY)
        self.assertIn('xServer.injectKeyRelease(key);', OVERLAY)
        self.assertIn('CharoiteGameControlProfiles', OVERLAY)
        self.assertNotIn('xServer.keyboard.onKeyEvent(new android.view.KeyEvent(', OVERLAY)
        for token in ('KEY_UP', 'KEY_Z', 'KEY_X', 'KEY_SHIFT_L', 'KEY_CTRL_L',
                      'KEY_ESC', 'KEY_ENTER'):
            self.assertIn('XKeycode.'+token, PROFILE)

    def test_each_pressed_button_and_shared_hold_is_counted(self):
        self.assertIn('final boolean[] down = {false};', CONTROLS)
        self.assertIn('if (down[0] != pressed)', CONTROLS)
        self.assertIn('final Map<Integer, Integer> held = new HashMap<>();', CONTROLS)
        self.assertIn('held.put(code, count + 1);', CONTROLS)
        self.assertIn('if (count == 0) sink.send(code, true);', CONTROLS)
        self.assertIn('if (count == 1)', CONTROLS)
        self.assertIn('sink.send(code, false);', CONTROLS)

    def test_read_only_discovery_and_editable_per_installation(self):
        self.assertIn('CharoiteGameControlProfiles.idForExecutable(child.getAbsolutePath())', DISCOVERY)
        self.assertIn('CharoiteGameControlProfiles.idForExecutable(executable)', SESSION)
        self.assertIn('CharoiteGameControlProfiles.showEditor(this, executable)', PORTAL)
        self.assertIn('getSharedPreferences("charoite_game_controls"', PROFILE)
        self.assertIn('path.replace(', PROFILE)
        self.assertIn('public static void reset(Context context, String path)', PROFILE)
        self.assertIn('generic_unverified', PROFILE)
        self.assertNotIn('container.saveData(', PROFILE)
        self.assertNotIn('deleteRecursively(', PROFILE)

if __name__ == "__main__":
    unittest.main()
